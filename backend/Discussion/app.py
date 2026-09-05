from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# MongoDB连接
client = MongoClient('mongodb://localhost:27017/')
db = client['omni_edu']


def _serialize_post(post):
    """把Mongo文档转成可JSON返回的结构"""
    post['_id'] = str(post['_id'])
    if 'created_at' in post and isinstance(post['created_at'], datetime):
        post['created_at'] = post['created_at'].isoformat()
    post.setdefault('likes', 0)
    post.setdefault('views', 0)
    post.setdefault('shares', 0)
    post['liked_by'] = [str(uid) for uid in post.get('liked_by', [])]
    post['favorited_by'] = [str(uid) for uid in post.get('favorited_by', [])]
    return post


@app.route('/api/discussions', methods=['GET'])
def get_discussions():
    """获取所有帖子（分页）"""
    user_id = (request.args.get('user_id') or '').strip()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    skip = (page - 1) * limit

    try:
        posts = list(db.discussions.find(
            {
                'parent_id': None,
                # 私密帖只对作者本人可见
                '$or': [
                    {'is_private': {'$ne': True}},
                    {'user_id': user_id} if user_id else {'is_private': {'$ne': True}}
                ]
            },
            sort=[('created_at', -1)],
            skip=skip,
            limit=limit
        ))

        total = db.discussions.count_documents({
            'parent_id': None,
            '$or': [
                {'is_private': {'$ne': True}},
                {'user_id': user_id} if user_id else {'is_private': {'$ne': True}}
            ]
        })

        for post in posts:
            post['reply_count'] = db.discussions.count_documents({'parent_id': str(post['_id'])})
            _serialize_post(post)
            post['is_liked'] = bool(user_id) and user_id in post['liked_by']
            post['is_favorited'] = bool(user_id) and user_id in post['favorited_by']

        return jsonify({
            'code': 200,
            'data': {
                'posts': posts,
                'total': total,
                'page': page,
                'pages': (total + limit - 1) // limit
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})


@app.route('/api/discussions', methods=['POST'])
def create_post():
    """发帖"""
    data = request.json
    user_id = data.get('user_id')
    username = data.get('username', '匿名用户')
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    is_private = bool(data.get('is_private', False))

    if not title or not content:
        return jsonify({'code': 400, 'message': '标题和内容不能为空'})

    try:
        post = {
            'user_id': user_id,
            'username': username,
            'title': title,
            'content': content,
            'parent_id': None,
            'is_private': is_private,
            'created_at': datetime.now(),
            'likes': 0,
            'liked_by': [],
            'favorited_by': [],
            'views': 0,
            'shares': 0
        }
        result = db.discussions.insert_one(post)
        post = _serialize_post(post)
        post['is_liked'] = False
        post['is_favorited'] = False

        return jsonify({'code': 200, 'message': '发布成功', 'data': post})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})


@app.route('/api/discussions/<post_id>', methods=['GET'])
def get_post_detail(post_id):
    """获取帖子详情及完整回复树"""
    user_id = (request.args.get('user_id') or '').strip()
    try:
        post = db.discussions.find_one({'_id': ObjectId(post_id)})
        if not post:
            return jsonify({'code': 404, 'message': '帖子不存在'})

        # 私密帖：仅作者本人可查看
        if post.get('is_private') and user_id != str(post.get('user_id') or ''):
            return jsonify({'code': 403, 'message': '该帖子为私密内容，仅作者可见'})

        # 浏览数 +1（同一会话内只算一次需要 cookie，这里简单 +1）
        db.discussions.update_one({'_id': ObjectId(post_id)}, {'$inc': {'views': 1}})

        # 递归拉所有后代回复
        all_items = {post_id: []}
        queue = [post_id]
        visited = set()
        while queue:
            current = queue.pop()
            if current in visited:
                continue
            visited.add(current)
            children = list(db.discussions.find({'parent_id': current}, sort=[('created_at', 1)]))
            all_items[current] = children
            for child in children:
                queue.append(str(child['_id']))

        # 构建嵌套结构
        def build_node(item):
            node = _serialize_post(item)
            cid = node['_id']
            node['is_liked'] = bool(user_id) and user_id in node['liked_by']
            node['is_favorited'] = bool(user_id) and user_id in node['favorited_by']
            node['replies'] = [build_node(c) for c in all_items.get(cid, [])]
            return node

        post['_id'] = str(post['_id'])
        if 'created_at' in post and isinstance(post['created_at'], datetime):
            post['created_at'] = post['created_at'].isoformat()
        post['liked_by'] = [str(uid) for uid in post.get('liked_by', [])]
        post['favorited_by'] = [str(uid) for uid in post.get('favorited_by', [])]
        post['is_liked'] = bool(user_id) and user_id in post['liked_by']
        post['is_favorited'] = bool(user_id) and user_id in post['favorited_by']
        post['replies'] = [build_node(c) for c in all_items.get(post_id, [])]

        return jsonify({'code': 200, 'data': post})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})


@app.route('/api/discussions/<post_id>/reply', methods=['POST'])
def add_reply(post_id):
    """回复帖子或回复某条回复（parent_id 指向任意 post_id）"""
    data = request.json
    user_id = data.get('user_id')
    username = data.get('username', '匿名用户')
    content = data.get('content', '').strip()
    reply_to_id = data.get('reply_to_id', post_id)  # 默认回复主帖

    if not content:
        return jsonify({'code': 400, 'message': '回复内容不能为空'})

    try:
        # 验证要回复的对象存在
        target = db.discussions.find_one({'_id': ObjectId(reply_to_id)})
        if not target:
            return jsonify({'code': 404, 'message': '回复目标不存在'})

        reply = {
            'user_id': user_id,
            'username': username,
            'title': '',
            'content': content,
            'parent_id': reply_to_id,
            'reply_to_username': target.get('username', ''),
            'created_at': datetime.now(),
            'likes': 0,
            'liked_by': [],
            'favorited_by': [],
            'views': 0,
            'shares': 0
        }
        result = db.discussions.insert_one(reply)
        reply = _serialize_post(reply)
        reply['is_liked'] = False
        reply['is_favorited'] = False
        reply['replies'] = []

        return jsonify({'code': 200, 'message': '回复成功', 'data': reply})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})


@app.route('/api/discussions/<post_id>/like', methods=['POST'])
def toggle_like(post_id):
    """切换式点赞：同一用户再次点击取消点赞"""
    data = request.json or {}
    user_id = (data.get('user_id') or '').strip()
    if not user_id:
        return jsonify({'code': 400, 'message': '需要登录'})

    try:
        post = db.discussions.find_one({'_id': ObjectId(post_id)})
        if not post:
            return jsonify({'code': 404, 'message': '帖子不存在'})

        liked_by = [str(uid) for uid in post.get('liked_by', [])]
        if user_id in liked_by:
            liked_by.remove(user_id)
            liked = False
        else:
            liked_by.append(user_id)
            liked = True

        db.discussions.update_one(
            {'_id': ObjectId(post_id)},
            {'$set': {'liked_by': liked_by, 'likes': len(liked_by)}}
        )

        return jsonify({
            'code': 200,
            'likes': len(liked_by),
            'is_liked': liked
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})


@app.route('/api/discussions/<post_id>/favorite', methods=['POST'])
def toggle_favorite(post_id):
    """切换式收藏"""
    data = request.json or {}
    user_id = (data.get('user_id') or '').strip()
    if not user_id:
        return jsonify({'code': 400, 'message': '需要登录'})

    try:
        post = db.discussions.find_one({'_id': ObjectId(post_id)})
        if not post:
            return jsonify({'code': 404, 'message': '帖子不存在'})

        favorited_by = [str(uid) for uid in post.get('favorited_by', [])]
        if user_id in favorited_by:
            favorited_by.remove(user_id)
            favorited = False
        else:
            favorited_by.append(user_id)
            favorited = True

        db.discussions.update_one(
            {'_id': ObjectId(post_id)},
            {'$set': {'favorited_by': favorited_by}}
        )

        return jsonify({
            'code': 200,
            'favorites': len(favorited_by),
            'is_favorited': favorited
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})


@app.route('/api/discussions/<post_id>/share', methods=['POST'])
def share_post(post_id):
    """转发：分享数 +1"""
    try:
        result = db.discussions.update_one(
            {'_id': ObjectId(post_id)},
            {'$inc': {'shares': 1}}
        )
        if result.modified_count == 0 and result.matched_count == 0:
            return jsonify({'code': 404, 'message': '帖子不存在'})

        post = db.discussions.find_one({'_id': ObjectId(post_id)})
        return jsonify({'code': 200, 'shares': post.get('shares', 0)})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})


@app.route('/api/discussions/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    """删除帖子（仅作者本人可删，连同所有后代回复一起删除）"""
    data = request.json or {}
    user_id = data.get('user_id')
    try:
        post = db.discussions.find_one({'_id': ObjectId(post_id)})
        if not post:
            return jsonify({'code': 404, 'message': '帖子不存在'})
        if not user_id or str(post.get('user_id') or '') != str(user_id):
            return jsonify({'code': 403, 'message': '只能删除自己的帖子'})

        # 递归删除所有后代
        to_delete = [post_id]
        queue = [post_id]
        visited = set()
        while queue:
            current = queue.pop()
            if current in visited:
                continue
            visited.add(current)
            children = list(db.discussions.find({'parent_id': current}, projection={'_id': 1}))
            for child in children:
                cid = str(child['_id'])
                to_delete.append(cid)
                queue.append(cid)

        object_ids = [ObjectId(i) for i in to_delete]
        db.discussions.delete_many({'_id': {'$in': object_ids}})
        return jsonify({'code': 200, 'message': '删除成功', 'deleted_count': len(to_delete)})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5020)
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port, debug=False)