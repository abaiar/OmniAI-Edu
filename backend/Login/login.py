from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

MONGODB_AVAILABLE = False
users_collection = None

try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    db = client['teacher_assistant']
    users_collection = db['users']
    MONGODB_AVAILABLE = True
    print("✅ MongoDB 连接成功")
except Exception as e:
    print(f"⚠️ MongoDB 连接失败: {e}")
    print("📝 使用内存模式运行（测试用）")

memory_users = {
    "teacher": {
        "username": "teacher",
        "password": generate_password_hash("123456"),
        "role": "teacher"
    },
    "admin": {
        "username": "admin",
        "password": generate_password_hash("admin123"),
        "role": "admin"
    },
    "student": {
        "username": "student",
        "password": generate_password_hash("123456"),
        "role": "student"
    }
}

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400

    if MONGODB_AVAILABLE:
        if users_collection.find_one({"username": username}):
            return jsonify({"success": False, "message": "该用户名已被注册"}), 409

        hashed_password = generate_password_hash(password)
        class_name = request.form.get('class_name', '')
        student_id = request.form.get('student_id', '')
        new_user = {
            "username": username,
            "password": hashed_password,
            "role": "teacher",
            "class_name": class_name,
            "student_id": student_id,
            "created_at": datetime.datetime.utcnow()
        }

        try:
            users_collection.insert_one(new_user)
            return jsonify({"success": True, "message": "注册成功，请登录"}), 201
        except Exception as e:
            print(f"注册错误: {e}")
            return jsonify({"success": False, "message": "注册失败，请稍后重试"}), 500
    else:
        if username in memory_users:
            return jsonify({"success": False, "message": "该用户名已被注册"}), 409
        
        memory_users[username] = {
            "username": username,
            "password": generate_password_hash(password),
            "role": "teacher",
            "class_name": class_name,
            "student_id": student_id
        }
        return jsonify({"success": True, "message": "注册成功，请登录（内存模式）"}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    print(f"收到登录请求: 用户名={username}")

    if not username or not password:
        return jsonify({"success": False, "message": "请输入用户名和密码"}), 400

    if MONGODB_AVAILABLE:
        user = users_collection.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            return jsonify({
                "success": True, 
                "message": "登录成功",
                "user": {
                    "username": user['username'],
                    "role": user.get('role', 'teacher'),
                    "token": "jwt-token-" + username
                }
            })
        else:
            return jsonify({"success": False, "message": "用户名或密码错误"}), 401
    else:
        user = memory_users.get(username)
        if user and check_password_hash(user['password'], password):
            return jsonify({
                "success": True, 
                "message": "登录成功（内存模式）",
                "user": {
                    "username": user['username'],
                    "role": user.get('role', 'teacher'),
                    "token": "jwt-token-" + username
                }
            })
        else:
            return jsonify({"success": False, "message": "用户名或密码错误"}), 401

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "mongodb": "connected" if MONGODB_AVAILABLE else "memory_mode",
        "message": "登录服务运行中"
    })

if __name__ == '__main__':
    print("=" * 50)
    print("🔐 登录服务启动")
    print("=" * 50)
    if not MONGODB_AVAILABLE:
        print("📝 内存模式 - 测试账号:")
        print("   用户名: teacher, 密码: 123456")
        print("   用户名: admin, 密码: admin123")
        print("   用户名: student, 密码: 123456")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
