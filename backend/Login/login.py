from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime

app = Flask(__name__)
CORS(app)

# 密钥
SECRET_KEY = 'your-secret-key-here'

# 硬编码用户（内存模式，无需MongoDB）
USERS = {
    'teacher': {
        'password': '123456',
        'role': 'teacher',
        'username': 'teacher'
    }
}

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请提供JSON格式的数据'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        user = USERS.get(username)
        if not user or user['password'] != password:
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
        token = jwt.encode({
            'username': username,
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'username': username,
                'role': user['role'],
                'token': token
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)