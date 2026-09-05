"""
AuthMulti — 多方式注册登录服务

支持：
- 手机号：阿里云短信 API 真实发送验证码
- 邮箱：QQ 邮箱 SMTP 真实发送验证码
- 微信：微信开放平台 OAuth 扫码登录（生成真实授权 URL，回调换取 openid）
- QQ：QQ 互联 OAuth 扫码登录（生成真实授权 URL，回调换取 openid）

所有第三方渠道都需要在 .env 中配置相应的 KEY / SECRET，未配置时返回清晰错误提示。
"""
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
from dotenv import load_dotenv
import hashlib
import random
import re
import os
import secrets
import urllib.parse
import smtplib
import ssl
from email.mime.text import MIMEText
from email.utils import formataddr

load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB连接
client = MongoClient('mongodb://localhost:27017/')
db = client['omni_edu']

# ====== 配置读取 ======
QQ_MAIL_USER = os.getenv('QQ_MAIL_USER', '')
QQ_MAIL_AUTH_CODE = os.getenv('QQ_MAIL_AUTH_CODE', '')

ALIYUN_ACCESS_KEY_ID = os.getenv('ALIYUN_ACCESS_KEY_ID', '')
ALIYUN_ACCESS_KEY_SECRET = os.getenv('ALIYUN_ACCESS_KEY_SECRET', '')
ALIYUN_SMS_SIGN_NAME = os.getenv('ALIYUN_SMS_SIGN_NAME', '')
ALIYUN_SMS_TEMPLATE_CODE = os.getenv('ALIYUN_SMS_TEMPLATE_CODE', '')

WECHAT_APP_ID = os.getenv('WECHAT_APP_ID', '')
WECHAT_APP_SECRET = os.getenv('WECHAT_APP_SECRET', '')

QQ_APP_ID = os.getenv('QQ_APP_ID', '')
QQ_APP_SECRET = os.getenv('QQ_APP_SECRET', '')

OAUTH_REDIRECT_BASE = os.getenv('OAUTH_REDIRECT_BASE', 'http://localhost:3000')


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def generate_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


# 验证码存储（生产环境建议用 Redis）
sms_codes = {}
email_codes = {}
qq_codes = {}
wechat_codes = {}

_CODE_STORES = {
    'phone': sms_codes,
    'email': email_codes,
    'qq': qq_codes,
    'wechat': wechat_codes,
}

# 账号类型 → 用户表字段
ACCOUNT_FIELDS = {
    'phone': 'phone',
    'email': 'email',
    'qq': 'qq_account',
    'wechat': 'wechat_account',
}


def detect_account_type(account):
    """识别账号类型：phone / email / qq / wechat（不支持返回 None）"""
    if re.match(r'^1[3-9]\d{9}$', account):
        return 'phone'
    if re.match(r'^[\w.-]+@[\w.-]+\.\w+$', account):
        return 'email'
    if re.match(r'^\d{5,11}$', account):
        return 'qq'
    if re.match(r'^[a-zA-Z][\w-]{1,19}$', account):
        return 'wechat'
    return None


def save_code(account, code):
    t = detect_account_type(account)
    if t:
        _CODE_STORES[t][account] = {'code': code, 'time': datetime.now()}


def check_code(account, code):
    t = detect_account_type(account)
    if not t:
        return False
    c = _CODE_STORES[t].get(account)
    return bool(c and c['code'] == code and (datetime.now() - c['time']) < timedelta(minutes=5))


def pop_code(account):
    for store in _CODE_STORES.values():
        store.pop(account, None)


def find_user_by_account(account):
    """按手机号/邮箱/QQ号/微信号/用户名查找用户"""
    if not account:
        return None
    t = detect_account_type(account)
    queries = [{'username': account}]
    if t:
        queries.append({ACCOUNT_FIELDS[t]: account})
    return db.users.find_one({'$or': queries})


# ====== 安全开关：调试模式是否允许前端拿到 debug_code ======
# 默认关闭。生产环境永远关闭，避免 QQ/微信调试码被前端获取。
# 本地开发如需在界面上看到调试码，可在 .env 加 DEV_RETURN_DEBUG_CODE=true
DEV_RETURN_DEBUG_CODE = os.getenv('DEV_RETURN_DEBUG_CODE', 'false').lower() in ('1', 'true', 'yes')


def _send_email_dev_hint(account, code):
    """调试模式：仅写日志，绝不返回 debug_code 给前端"""
    try:
        with open('email_debug_codes.log', 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now().isoformat()}] {account} -> {code}\n')
    except Exception:
        pass


def _send_sms_dev_hint(account, code):
    try:
        with open('sms_debug_codes.log', 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now().isoformat()}] {account} -> {code}\n')
    except Exception:
        pass

# OAuth state 存储（防 CSRF）
oauth_states = {}


# ========================================================
# 邮件真实发送（QQ 邮箱 SMTP）
# ========================================================
def send_email_code_real(account, code):
    """通过 QQ 邮箱 SMTP 真实发送验证码"""
    if not QQ_MAIL_USER or not QQ_MAIL_AUTH_CODE:
        raise RuntimeError('未配置 QQ_MAIL_USER / QQ_MAIL_AUTH_CODE，无法发送邮件验证码')

    subject = '【AI通识教育平台】您的验证码'
    body = f'''您好！

您正在使用邮箱注册/登录 AI通识教育平台，验证码如下：

    {code}

该验证码 5 分钟内有效，请尽快使用。如非本人操作，请忽略此邮件。

—— AI通识教育平台'''
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = formataddr(['AI通识教育平台', QQ_MAIL_USER])
    msg['To'] = account

    # QQ 邮箱 SMTP_SSL 465 / STARTTLS 587
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.qq.com', 465, context=context, timeout=10) as server:
        server.login(QQ_MAIL_USER, QQ_MAIL_AUTH_CODE)
        server.sendmail(QQ_MAIL_USER, [account], msg.as_string())


# ========================================================
# 短信真实发送（阿里云短信 API）
# ========================================================
def send_sms_code_real(phone, code):
    """通过阿里云短信 API 真实发送验证码"""
    if not all([ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, ALIYUN_SMS_SIGN_NAME, ALIYUN_SMS_TEMPLATE_CODE]):
        raise RuntimeError('未配置阿里云短信相关环境变量，无法发送短信验证码')

    # 使用阿里云 OpenAPI 直接调用（避免额外 SDK 安装）
    from urllib.request import Request, urlopen
    import json as _json
    import hmac
    import hashlib as _hashlib
    import base64
    import time as _time

    # 这里实现简化版阿里云短信签名 + 调用
    # 完整签名算法参考：https://help.aliyun.com/zh/sms/developer-reference/api-reference-send-sms
    # 模板参数 {"code": code}
    params = {
        'PhoneNumbers': phone,
        'SignName': ALIYUN_SMS_SIGN_NAME,
        'TemplateCode': ALIYUN_SMS_TEMPLATE_CODE,
        'TemplateParam': _json.dumps({'code': code})
    }

    # 调用 API 网关
    host = 'dysmsapi.aliyuncs.com'
    canonical_query = '&'.join(f'{k}={urllib.parse.quote_plus(str(v))}' for k, v in sorted(params.items()))
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    canonical_headers = f'x-acs-action:SendSms\nx-acs-date:{now}\nx-acs-version:2017-05-25\n'
    signed_headers = 'x-acs-action;x-acs-date;x-acs-version'
    hashed_request_payload = _hashlib.sha256(''.encode()).hexdigest()
    canonical_request = (
        f'POST\n'
        f'/\n'
        f'{canonical_query}\n'
        f'{canonical_headers}\n'
        f'{signed_headers}\n'
        f'{hashed_request_payload}'
    )

    string_to_sign = (
        f'ACS3-HMAC-SHA256\n'
        f'{_hashlib.sha256(canonical_request.encode()).hexdigest()}\n'
    )
    signature = base64.b64encode(
        hmac.new(ALIYUN_ACCESS_KEY_SECRET.encode(), string_to_sign.encode(), _hashlib.sha256).digest()
    ).decode()

    authorization = (
        f'ACS3-HMAC-SHA256 Credential={ALIYUN_ACCESS_KEY_ID},'
        f'SignedHeaders={signed_headers},Signature={signature}'
    )

    req = Request(
        url=f'https://{host}/?{canonical_query}',
        data=''.encode(),
        headers={
            'Authorization': authorization,
            'x-acs-action': 'SendSms',
            'x-acs-date': now,
            'x-acs-version': '2017-05-25',
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        method='POST'
    )

    with urlopen(req, timeout=10) as resp:
        result = _json.loads(resp.read().decode())

    if result.get('Code') != 'OK':
        raise RuntimeError(f'阿里云短信发送失败：{result.get("Message", result)}')

    return result


# ========================================================
# 微信 OAuth
# ========================================================
@app.route('/api/auth/wechat/url', methods=['GET'])
def wechat_login_url():
    """生成微信扫码登录 URL"""
    if not WECHAT_APP_ID:
        return jsonify({'code': 503, 'message': '微信登录未配置：请在 .env 中设置 WECHAT_APP_ID / WECHAT_APP_SECRET'})
    state = secrets.token_urlsafe(16)
    oauth_states[state] = {'channel': 'wechat', 'time': datetime.now()}
    redirect_uri = f'{OAUTH_REDIRECT_BASE}/api/auth/wechat/callback'
    auth_url = (
        f'https://open.weixin.qq.com/connect/qrconnect?'
        f'appid={WECHAT_APP_ID}&redirect_uri={urllib.parse.quote(redirect_uri)}&'
        f'response_type=code&scope=snsapi_login&state={state}'
        f'#wechat_redirect'
    )
    return jsonify({'code': 200, 'auth_url': auth_url, 'state': state})


@app.route('/api/auth/wechat/callback', methods=['GET'])
def wechat_callback():
    """微信 OAuth 回调：code → access_token → openid"""
    code = request.args.get('code')
    state = request.args.get('state', '')
    if not code or state not in oauth_states:
        return redirect(f'{OAUTH_REDIRECT_BASE}/auth?error=wechat_invalid')
    if not WECHAT_APP_ID or not WECHAT_APP_SECRET:
        return redirect(f'{OAUTH_REDIRECT_BASE}/auth?error=wechat_unconfigured')

    from urllib.request import urlopen
    import json as _json

    token_url = (
        f'https://api.weixin.qq.com/sns/oauth2/access_token?'
        f'appid={WECHAT_APP_ID}&secret={WECHAT_APP_SECRET}&code={code}&grant_type=authorization_code'
    )
    try:
        with urlopen(token_url, timeout=10) as r:
            token_data = _json.loads(r.read().decode())
    except Exception as e:
        return redirect(f'{OAUTH_REDIRECT_BASE}/auth?error=wechat_token_failed&detail={urllib.parse.quote(str(e))}')

    if 'openid' not in token_data:
        return redirect(f'{OAUTH_REDIRECT_BASE}/auth?error=wechat_no_openid&detail={urllib.parse.quote(str(token_data))}')

    openid = token_data['openid']
    # 创建或获取用户
    user = db.users.find_one({'bind_wechat': openid})
    if not user:
        user = {
            'username': f'微信用户{openid[-4:]}',
            'password': '',
            'phone': '',
            'email': '',
            'bind_wechat': openid,
            'bind_qq': '',
            'created_at': datetime.now(),
            'avatar': ''
        }
        result = db.users.insert_one(user)
        user['_id'] = str(result.inserted_id)
    else:
        user['_id'] = str(user['_id'])
    user.pop('password', None)
    user['_id_str'] = user['_id']
    del oauth_states[state]
    # 跳转回前端，携带用户信息
    import json as _json
    user_json = urllib.parse.quote(_json.dumps({'id': user['_id'], 'username': user.get('username', '')}))
    return redirect(f'{OAUTH_REDIRECT_BASE}/auth?wechat_login=1&user={user_json}')


# ========================================================
# QQ OAuth
# ========================================================
@app.route('/api/auth/qq/url', methods=['GET'])
def qq_login_url():
    """生成 QQ 扫码登录 URL"""
    if not QQ_APP_ID:
        return jsonify({'code': 503, 'message': 'QQ登录未配置：请在 .env 中设置 QQ_APP_ID / QQ_APP_SECRET'})
    state = secrets.token_urlsafe(16)
    oauth_states[state] = {'channel': 'qq', 'time': datetime.now()}
    redirect_uri = f'{OAUTH_REDIRECT_BASE}/api/auth/qq/callback'
    auth_url = (
        f'https://graph.qq.com/oauth2.0/authorize?'
        f'response_type=code&client_id={QQ_APP_ID}&redirect_uri={urllib.parse.quote(redirect_uri)}&'
        f'state={state}'
    )
    return jsonify({'code': 200, 'auth_url': auth_url, 'state': state})


@app.route('/api/auth/qq/callback', methods=['GET'])
def qq_callback():
    """QQ OAuth 回调：code → access_token → openid"""
    code = request.args.get('code')
    state = request.args.get('state', '')
    if not code or state not in oauth_states:
        return redirect(f'{OAUTH_REDIRECT_BASE}/auth?error=qq_invalid')
    if not QQ_APP_ID or not QQ_APP_SECRET:
        return redirect(f'{OAUTH_REDIRECT_BASE}/auth?error=qq_unconfigured')

    from urllib.request import urlopen
    import json as _json

    token_url = (
        f'https://graph.qq.com/oauth2.0/token?'
        f'grant_type=authorization_code&client_id={QQ_APP_ID}&client_secret={QQ_APP_SECRET}&'
        f'code={code}&redirect_uri={urllib.parse.quote(OAUTH_REDIRECT_BASE + "/api/auth/qq/callback")}'
    )
    try:
        with urlopen(token_url, timeout=10) as r:
            token_resp = r.read().decode()
        # 响应是 text/plain，如 access_token=xxx&expires_in=xxx
        token_data = dict(urllib.parse.parse_qsl(token_resp))
        access_token = token_data.get('access_token')
        if not access_token:
            return redirect(f'{OAUTH_REDIRECT_BASE}/auth?error=qq_no_token&detail={urllib.parse.quote(token_resp)}')

        # 获取 openid
        with urlopen(f'https://graph.qq.com/oauth2.0/me?access_token={access_token}', timeout=10) as r:
            me_resp = r.read().decode()
        # callback( {"client_id":"...","openid":"..."} );
        m = re.search(r'\(\s*({.*?})\s*\)', me_resp)
        if not m:
            return redirect(f'{OAUTH_REDIRECT_BASE}/auth?error=qq_me_failed&detail={urllib.parse.quote(me_resp)}')
        me_data = _json.loads(m.group(1))
        openid = me_data.get('openid')
        if not openid:
            return redirect(f'{OAUTH_REDIRECT_BASE}/auth?error=qq_no_openid')
    except Exception as e:
        return redirect(f'{OAUTH_REDIRECT_BASE}/auth?error=qq_token_failed&detail={urllib.parse.quote(str(e))}')

    user = db.users.find_one({'bind_qq': openid})
    if not user:
        user = {
            'username': f'QQ用户{openid[-4:]}',
            'password': '',
            'phone': '',
            'email': '',
            'bind_wechat': '',
            'bind_qq': openid,
            'created_at': datetime.now(),
            'avatar': ''
        }
        result = db.users.insert_one(user)
        user['_id'] = str(result.inserted_id)
    else:
        user['_id'] = str(user['_id'])
    user.pop('password', None)
    user['_id_str'] = user['_id']
    del oauth_states[state]
    user_json = urllib.parse.quote(_json.dumps({'id': user['_id'], 'username': user.get('username', '')}))
    return redirect(f'{OAUTH_REDIRECT_BASE}/auth?qq_login=1&user={user_json}')


# ========================================================
# 验证码发送（带调试模式兜底：未配置凭证时也能用）
# ========================================================
def _dev_mode_email(account, code):
    """未配置 SMTP 时：把验证码写到本地文件 + 返回给前端，避免完全跑不通"""
    try:
        with open('email_debug_codes.log', 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now().isoformat()}] {account} -> {code}\n')
    except Exception:
        pass
    return {'debug_code': code, 'dev_mode': True}


def _dev_mode_sms(phone, code):
    try:
        with open('sms_debug_codes.log', 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now().isoformat()}] {phone} -> {code}\n')
    except Exception:
        pass
    return {'debug_code': code, 'dev_mode': True}


@app.route('/api/auth/send-code', methods=['POST'])
def send_code():
    """发送验证码：手机走短信、邮箱走 SMTP、QQ号/微信号走调试模式（无真实通道）。

    【安全加固】任意账号能发码 → 拿到码就能改密码。修复：
    1. 重置密码场景：必须校验账号已存在 → 不存在返回 404
    2. 调试模式（QQ/微信）默认不再返回 debug_code 给前端，避免攻击者用任意 QQ 号改别人密码
       如需在本地界面看到码，设置环境变量 DEV_RETURN_DEBUG_CODE=true
    3. 请求体支持 purpose=register|reset|null：
       - reset（默认）：账号必须存在，且 QQ/微信不允许（必须用对应渠道登录）
       - register：账号可以不存在（用于注册前发码）；验证码作用域不绑定已注册用户
    """
    data = request.json
    account = data.get('account', '').strip()
    purpose = data.get('purpose', 'reset')  # register / reset
    if not account:
        return jsonify({'code': 400, 'message': '请输入QQ号/微信号/邮箱/手机号'})

    acct_type = detect_account_type(account)
    if not acct_type:
        return jsonify({'code': 400, 'message': '账号格式不正确（支持QQ号/微信号/邮箱/手机号）'})

    # ======== 重置密码场景安全校验 ========
    if purpose == 'reset':
        user = find_user_by_account(account)
        if not user:
            return jsonify({'code': 404, 'message': '该账号未注册，无法发送验证码'})
        # 该账号必须是 phone 或 email 类型；QQ/微信号注册的账号无密码可重置
        if acct_type in ('qq', 'wechat'):
            return jsonify({
                'code': 403,
                'message': f'该账号是{"QQ" if acct_type == "qq" else "微信"}快捷登录注册，不支持通过验证码重置密码，请用QQ/微信扫码重新登录',
                'channel': acct_type,
                'unsupported_reset': True
            })
    # 注册场景：不需要预校验（账号尚未存在），但还是限制类型
    # 注册流程还是需要走到对应字段

    code = generate_code()
    save_code(account, code)

    # === QQ 号：无真实发送通道，直接调试模式 ===
    if acct_type == 'qq':
        _send_sms_dev_hint(account, code)
        payload = {'dev_mode': True}
        if DEV_RETURN_DEBUG_CODE:
            payload['debug_code'] = code
        return jsonify({
            'code': 200,
            'message': '验证码已生成（QQ账号为调试模式，验证码见界面提示）',
            'channel': 'qq',
            **payload
        })

    # === 微信号：无真实发送通道，直接调试模式 ===
    if acct_type == 'wechat':
        _send_sms_dev_hint(account, code)
        payload = {'dev_mode': True}
        if DEV_RETURN_DEBUG_CODE:
            payload['debug_code'] = code
        return jsonify({
            'code': 200,
            'message': '验证码已生成（微信账号为调试模式，验证码见界面提示）',
            'channel': 'wechat',
            **payload
        })

    if acct_type == 'phone':
        if all([ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, ALIYUN_SMS_SIGN_NAME, ALIYUN_SMS_TEMPLATE_CODE]):
            try:
                send_sms_code_real(account, code)
                return jsonify({
                    'code': 200,
                    'message': f'验证码已发送至手机 {account[:3]}****{account[-4:]}',
                    'channel': 'sms'
                })
            except Exception:
                _send_sms_dev_hint(account, code)
                payload = {'dev_mode': True}
                if DEV_RETURN_DEBUG_CODE:
                    payload['debug_code'] = code
                return jsonify({
                    'code': 200,
                    'message': '短信通道暂不可用，已启用调试模式',
                    'channel': 'sms',
                    **payload
                })
        else:
            _send_sms_dev_hint(account, code)
            payload = {'dev_mode': True}
            if DEV_RETURN_DEBUG_CODE:
                payload['debug_code'] = code
            return jsonify({
                'code': 200,
                'message': '验证码已生成（调试模式：未配置短信凭证）',
                'channel': 'sms',
                **payload
            })

    # === 邮箱 ===
    if QQ_MAIL_USER and QQ_MAIL_AUTH_CODE:
        try:
            send_email_code_real(account, code)
            return jsonify({
                'code': 200,
                'message': f'验证码已发送至邮箱 {account}',
                'channel': 'email'
            })
        except Exception:
            _send_email_dev_hint(account, code)
            payload = {'dev_mode': True}
            if DEV_RETURN_DEBUG_CODE:
                payload['debug_code'] = code
            return jsonify({
                'code': 200,
                'message': '邮件发送失败，已启用调试模式',
                'channel': 'email',
                **payload
            })
    else:
        _send_email_dev_hint(account, code)
        payload = {'dev_mode': True}
        if DEV_RETURN_DEBUG_CODE:
            payload['debug_code'] = code
        return jsonify({
            'code': 200,
            'message': '验证码已生成（调试模式：未配置邮箱凭证）',
            'channel': 'email',
            **payload
        })


# ========================================================
# 注册
# ========================================================
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    method = data.get('method', 'password')

    if method == 'password':
        username = data.get('username', '').strip()
        password = data.get('password', '')
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()

        if not username or not password:
            return jsonify({'code': 400, 'message': '用户名和密码不能为空'})
        if len(password) < 6:
            return jsonify({'code': 400, 'message': '密码至少6位'})

        # 检查用户名（以及可选的手机号/邮箱）是否已被占用
        or_queries = [{'username': username}]
        if phone:
            or_queries.append({'phone': phone})
        if email:
            or_queries.append({'email': email})
        existing = db.users.find_one({'$or': or_queries})
        if existing:
            return jsonify({'code': 409, 'message': '用户名/手机号/邮箱已被注册'})

        user = {
            'username': username,
            'password': hash_password(password),
            'phone': phone,
            'email': email,
            'qq_account': '',
            'wechat_account': '',
            'bind_wechat': '',
            'bind_qq': '',
            'created_at': datetime.now(),
            'avatar': '',
            'bio': ''
        }
        result = db.users.insert_one(user)
        user['_id'] = str(result.inserted_id)
        del user['password']
        return jsonify({'code': 200, 'message': '注册成功', 'data': user})

    elif method == 'code':
        account = data.get('account', '').strip()
        code = data.get('code', '').strip()
        password = data.get('password', '')

        acct_type = detect_account_type(account)
        if not acct_type:
            return jsonify({'code': 400, 'message': '账号格式不正确（支持QQ号/微信号/邮箱/手机号）'})

        if not check_code(account, code):
            return jsonify({'code': 403, 'message': '验证码错误或已过期'})

        # 检查账号是否已被注册（按类型对应字段 + 用户名）
        field = ACCOUNT_FIELDS[acct_type]
        existing = db.users.find_one({'$or': [{field: account}, {'username': account}]})
        if existing:
            return jsonify({'code': 409, 'message': '该账号已被注册'})

        if acct_type == 'phone':
            prefix = '用户'
        elif acct_type == 'email':
            prefix = '用户'
        elif acct_type == 'qq':
            prefix = 'QQ用户'
        else:
            prefix = '微信用户'

        user = {
            'username': f'{prefix}{account[-4:]}',
            'password': hash_password(password) if password else '',
            'phone': account if acct_type == 'phone' else '',
            'email': account if acct_type == 'email' else '',
            'qq_account': account if acct_type == 'qq' else '',
            'wechat_account': account if acct_type == 'wechat' else '',
            'bind_wechat': '',
            'bind_qq': '',
            'created_at': datetime.now(),
            'avatar': '',
            'bio': ''
        }
        result = db.users.insert_one(user)
        user['_id'] = str(result.inserted_id)
        del user['password']

        pop_code(account)

        return jsonify({'code': 200, 'message': '注册成功', 'data': user})


# ========================================================
# 登录
# ========================================================
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    method = data.get('method', 'password')

    if method == 'password':
        account = data.get('account', '').strip()
        password = data.get('password', '')

        if not account or not password:
            return jsonify({'code': 400, 'message': '请输入账号和密码'})

        user = find_user_by_account(account)

        if not user or user.get('password') != hash_password(password):
            return jsonify({'code': 401, 'message': '账号或密码错误'})

        user['_id'] = str(user['_id'])
        del user['password']
        return jsonify({'code': 200, 'message': '登录成功', 'data': user})

    elif method == 'code':
        account = data.get('account', '').strip()
        code = data.get('code', '').strip()

        if not check_code(account, code):
            return jsonify({'code': 403, 'message': '验证码错误或已过期'})

        user = find_user_by_account(account)

        if not user:
            return jsonify({'code': 404, 'message': '该账号未注册，请先注册'})

        pop_code(account)

        user['_id'] = str(user['_id'])
        del user['password']
        return jsonify({'code': 200, 'message': '登录成功', 'data': user})

    elif method == 'wechat':
        openid = data.get('openid', '')
        if not openid:
            return jsonify({'code': 400, 'message': '微信授权失败'})
        user = db.users.find_one({'bind_wechat': openid})
        if not user:
            user = {
                'username': f'微信用户{openid[-4:]}',
                'password': '',
                'phone': '', 'email': '',
                'bind_wechat': openid, 'bind_qq': '',
                'created_at': datetime.now(), 'avatar': ''
            }
            result = db.users.insert_one(user)
            user['_id'] = str(result.inserted_id)
        else:
            user['_id'] = str(user['_id'])
            del user['password']
        return jsonify({'code': 200, 'message': '微信登录成功', 'data': user})

    elif method == 'qq':
        qq_openid = data.get('qq_openid', '')
        if not qq_openid:
            return jsonify({'code': 400, 'message': 'QQ授权失败'})
        user = db.users.find_one({'bind_qq': qq_openid})
        if not user:
            user = {
                'username': f'QQ用户{qq_openid[-4:]}',
                'password': '',
                'phone': '', 'email': '',
                'bind_wechat': '', 'bind_qq': qq_openid,
                'created_at': datetime.now(), 'avatar': ''
            }
            result = db.users.insert_one(user)
            user['_id'] = str(result.inserted_id)
        else:
            user['_id'] = str(user['_id'])
            del user['password']
        return jsonify({'code': 200, 'message': 'QQ登录成功', 'data': user})


@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """忘记密码：通过账号收到的验证码重置密码。

    【安全加固】任意账号都能触发 send-code 和 reset，这是严重漏洞。
    修复：
    1. 账号必须存在才能重置
    2. QQ/微信注册的账号不支持重置密码（无真实通道，防调试码泄露）
    3. 用户名形式的账号不允许重置（避免通过用户名匹配到其他字段）
    """
    data = request.json
    account = data.get('account', '').strip()
    code = data.get('code', '').strip()
    new_password = data.get('new_password', '')

    if not account or not code or not new_password:
        return jsonify({'code': 400, 'message': '参数不完整'})
    if len(new_password) < 6:
        return jsonify({'code': 400, 'message': '密码至少6位'})

    # 校验账号类型（必须是手机/邮箱，不接受用户名、QQ号/微信号）
    acct_type = detect_account_type(account)
    if acct_type not in ('phone', 'email'):
        return jsonify({
            'code': 403,
            'message': '只支持通过注册时绑定的手机号或邮箱重置密码'
        })

    # 校验账号存在
    user = find_user_by_account(account)
    if not user:
        return jsonify({'code': 404, 'message': '该账号未注册，无法重置密码'})

    if not check_code(account, code):
        return jsonify({'code': 403, 'message': '验证码错误或已过期'})

    db.users.update_one(
        {'_id': user['_id']},
        {'$set': {'password': hash_password(new_password)}}
    )

    pop_code(account)

    return jsonify({'code': 200, 'message': '密码重置成功，请使用新密码登录'})


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5021)
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port, debug=False)