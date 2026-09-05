"""
Social — 社交服务（个人主页 / 关注粉丝 / 私信）

端口 5022，与讨论区共用 MongoDB 的 omni_edu 库：
- users:           用户（AuthMulti 写入）
- discussions:     帖子/回复（Discussion 服务写入，含 is_private 字段）
- follows:         关注关系 {follower, followee, created_at}
- messages:        私信 {from_user, to_user, content, read, created_at}
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)
CORS(app)

client = MongoClient('mongodb://localhost:27017/')
db = client['omni_edu']


def _serialize_post(post):
    post['_id'] = str(post['_id'])
    if isinstance(post.get('created_at'), datetime):
        post['created_at'] = post['created_at'].isoformat()
    post.setdefault('likes', 0)
    post.setdefault('views', 0)
    post.pop('liked_by', None)
    post.pop('favorited_by', None)
    return post


# ========================================================
# 个人主页
# ========================================================
@app.route('/api/social/profile/<username>', methods=['GET'])
def get_profile(username):
    """个人主页：用户信息 + 关注/粉丝/获赞/收藏/浏览/帖子数统计"""
    viewer_id = (request.args.get('viewer_id') or '').strip()

    user = db.users.find_one({'username': username})
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'})

    # 帖子统计（主帖 + 回复都算获赞/浏览）
    agg = list(db.discussions.aggregate([
        {'$match': {'username': username}},
        {'$group': {
            '_id': None,
            'likes': {'$sum': {'$ifNull': ['$likes', 0]}},
            'views': {'$sum': {'$ifNull': ['$views', 0]}},
            'favorites': {'$sum': {'$size': {'$ifNull': ['$favorited_by', []]}}},
            'posts': {'$sum': {'$cond': [{'$eq': [{'$ifNull': ['$parent_id', None]}, None]}, 1, 0]}}
        }}
    ]))
    stats = agg[0] if agg else {}

    following_count = db.follows.count_documents({'follower': username})
    followers_count = db.follows.count_documents({'followee': username})

    is_self = bool(viewer_id) and str(user.get('_id')) == viewer_id
    is_following = False
    if viewer_id and not is_self:
        viewer = db.users.find_one({'_id': ObjectId(viewer_id)}) if ObjectId.is_valid(viewer_id) else None
        if viewer:
            is_following = db.follows.find_one({
                'follower': viewer.get('username'), 'followee': username
            }) is not None

    return jsonify({
        'code': 200,
        'data': {
            'user': {
                'id': str(user['_id']),
                'username': user.get('username', ''),
                'avatar': user.get('avatar', ''),
                'bio': user.get('bio', ''),
                'created_at': user.get('created_at').isoformat() if isinstance(user.get('created_at'), datetime) else None
            },
            'stats': {
                'following': following_count,
                'followers': followers_count,
                'likes_received': stats.get('likes', 0),
                'favorites_received': stats.get('favorites', 0),
                'views': stats.get('views', 0),
                'posts': stats.get('posts', 0)
            },
            'is_self': is_self,
            'is_following': is_following
        }
    })


@app.route('/api/social/profile/<username>/bio', methods=['POST'])
def update_bio(username):
    """修改个人简介（仅本人）"""
    data = request.json or {}
    user_id = (data.get('user_id') or '').strip()
    bio = (data.get('bio') or '').strip()[:200]

    if not user_id or not ObjectId.is_valid(user_id):
        return jsonify({'code': 401, 'message': '需要登录'})
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user or user.get('username') != username:
        return jsonify({'code': 403, 'message': '只能修改自己的简介'})

    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'bio': bio}})
    return jsonify({'code': 200, 'message': '简介已更新', 'data': {'bio': bio}})


# ========================================================
# 关注 / 粉丝
# ========================================================
@app.route('/api/social/follow', methods=['POST'])
def toggle_follow():
    """关注/取消关注（切换式）"""
    data = request.json or {}
    user_id = (data.get('user_id') or '').strip()
    target_username = (data.get('target_username') or '').strip()

    if not user_id or not ObjectId.is_valid(user_id):
        return jsonify({'code': 401, 'message': '需要登录'})
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return jsonify({'code': 401, 'message': '用户不存在'})
    me = user.get('username', '')
    if me == target_username:
        return jsonify({'code': 400, 'message': '不能关注自己'})

    target = db.users.find_one({'username': target_username})
    if not target:
        return jsonify({'code': 404, 'message': '目标用户不存在'})

    existing = db.follows.find_one({'follower': me, 'followee': target_username})
    if existing:
        db.follows.delete_one({'_id': existing['_id']})
        return jsonify({'code': 200, 'message': '已取消关注', 'data': {'following': False}})
    else:
        db.follows.insert_one({'follower': me, 'followee': target_username, 'created_at': datetime.now()})
        return jsonify({'code': 200, 'message': '关注成功', 'data': {'following': True}})


@app.route('/api/social/follow/list/<username>', methods=['GET'])
def follow_list(username):
    """关注列表 / 粉丝列表"""
    ftype = request.args.get('type', 'following')  # following | followers
    if ftype == 'followers':
        docs = db.follows.find({'followee': username})
        names = [d['follower'] for d in docs]
    else:
        docs = db.follows.find({'follower': username})
        names = [d['followee'] for d in docs]

    users = []
    for name in names:
        u = db.users.find_one({'username': name}, {'username': 1, 'avatar': 1, 'bio': 1})
        if u:
            users.append({'username': u['username'], 'avatar': u.get('avatar', ''), 'bio': u.get('bio', '')})
    return jsonify({'code': 200, 'data': {'type': ftype, 'users': users}})


# ========================================================
# 用户内容（公开 / 私密 分栏）
# ========================================================
@app.route('/api/social/posts/<username>', methods=['GET'])
def user_posts(username):
    """用户的主帖，按 公开/私密 分栏。私密仅本人可见。"""
    viewer_id = (request.args.get('viewer_id') or '').strip()

    user = db.users.find_one({'username': username})
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'})
    is_self = bool(viewer_id) and str(user['_id']) == viewer_id

    query = {'username': username, 'parent_id': None}
    if not is_self:
        query['is_private'] = {'$ne': True}

    posts = [ _serialize_post(p) for p in db.discussions.find(query, sort=[('created_at', -1)]) ]

    public = [p for p in posts if not p.get('is_private')]
    private = [p for p in posts if p.get('is_private')]

    return jsonify({'code': 200, 'data': {
        'is_self': is_self,
        'public': public,
        'private': private if is_self else []
    }})


@app.route('/api/social/posts/<post_id>/visibility', methods=['POST'])
def toggle_visibility(post_id):
    """公开 ⇆ 私密 切换（仅作者本人）"""
    data = request.json or {}
    user_id = (data.get('user_id') or '').strip()

    try:
        post = db.discussions.find_one({'_id': ObjectId(post_id)})
    except Exception:
        return jsonify({'code': 400, 'message': '参数错误'})
    if not post:
        return jsonify({'code': 404, 'message': '帖子不存在'})
    if not user_id or str(post.get('user_id') or '') != user_id:
        return jsonify({'code': 403, 'message': '只能操作自己的帖子'})

    new_val = not post.get('is_private', False)
    db.discussions.update_one({'_id': ObjectId(post_id)}, {'$set': {'is_private': new_val}})
    return jsonify({'code': 200, 'message': '已设为私密' if new_val else '已设为公开',
                    'data': {'is_private': new_val}})


# ========================================================
# 私信（已读 / 未读）
# ========================================================
@app.route('/api/social/messages', methods=['POST'])
def send_message():
    data = request.json or {}
    from_user = (data.get('from_user') or '').strip()
    to_user = (data.get('to_user') or '').strip()
    content = (data.get('content') or '').strip()

    if not from_user or not to_user or not content:
        return jsonify({'code': 400, 'message': '参数不完整'})
    if from_user == to_user:
        return jsonify({'code': 400, 'message': '不能给自己发私信'})

    target = db.users.find_one({'username': to_user})
    if not target:
        return jsonify({'code': 404, 'message': '对方用户不存在'})

    msg = {
        'from_user': from_user,
        'to_user': to_user,
        'content': content[:2000],
        'read': False,
        'created_at': datetime.now()
    }
    result = db.messages.insert_one(msg)
    msg['_id'] = str(result.inserted_id)
    msg['created_at'] = msg['created_at'].isoformat()
    return jsonify({'code': 200, 'message': '发送成功', 'data': msg})


@app.route('/api/social/messages/conversations/<username>', methods=['GET'])
def conversations(username):
    """会话列表：每个对话人的最后一条消息 + 未读数"""
    msgs = list(db.messages.find(
        {'$or': [{'from_user': username}, {'to_user': username}]},
        sort=[('created_at', -1)]
    ))

    convs = {}
    for m in msgs:
        peer = m['to_user'] if m['from_user'] == username else m['from_user']
        if peer not in convs:
            convs[peer] = {
                'peer': peer,
                'last_content': m['content'],
                'last_time': m['created_at'].isoformat() if isinstance(m['created_at'], datetime) else str(m['created_at']),
                'last_from_me': m['from_user'] == username,
                'unread': 0
            }
        if m['to_user'] == username and not m.get('read'):
            convs[peer]['unread'] += 1

    # 按最后消息时间倒序
    result = sorted(convs.values(), key=lambda c: c['last_time'], reverse=True)
    return jsonify({'code': 200, 'data': {'conversations': result}})


@app.route('/api/social/messages/chat/<username>/<peer>', methods=['GET'])
def chat_detail(username, peer):
    """两人的完整聊天记录，并把对方发给我的标记为已读"""
    msgs = list(db.messages.find(
        {'$or': [
            {'from_user': username, 'to_user': peer},
            {'from_user': peer, 'to_user': username}
        ]},
        sort=[('created_at', 1)]
    ))

    # 标记对方发来的为已读
    db.messages.update_many(
        {'from_user': peer, 'to_user': username, 'read': False},
        {'$set': {'read': True}}
    )

    out = []
    for m in msgs:
        out.append({
            '_id': str(m['_id']),
            'from_user': m['from_user'],
            'to_user': m['to_user'],
            'content': m['content'],
            'read': m.get('read', False),
            'created_at': m['created_at'].isoformat() if isinstance(m['created_at'], datetime) else str(m['created_at'])
        })
    return jsonify({'code': 200, 'data': {'messages': out}})


@app.route('/api/social/messages/unread/<username>', methods=['GET'])
def unread_count(username):
    count = db.messages.count_documents({'to_user': username, 'read': False})
    return jsonify({'code': 200, 'data': {'unread': count}})


# ========================================================
# 用户搜索（私信找人用）
# ========================================================
@app.route('/api/social/users/search', methods=['GET'])
def search_users():
    kw = (request.args.get('q') or '').strip()
    if not kw:
        return jsonify({'code': 200, 'data': {'users': []}})
    docs = db.users.find(
        {'username': {'$regex': kw, '$options': 'i'}},
        {'username': 1, 'avatar': 1, 'bio': 1}
    ).limit(10)
    users = [{'username': d['username'], 'avatar': d.get('avatar', ''), 'bio': d.get('bio', '')} for d in docs]
    return jsonify({'code': 200, 'data': {'users': users}})


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5022)
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port, debug=False)
