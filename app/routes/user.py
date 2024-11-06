from flask import Blueprint, request, jsonify
from app import db  # 确保正确导入你的数据库实例
from app.models import User, Bot  # 确保正确导入你的 User 和 Bot 模型
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.routes.auth import get_user
from app.models import User
import uuid

user = Blueprint('user', __name__)

def get_user_by_id(uuid):
    return User.query.filter_by(id=uuid).first()

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

def get_user_by_username_deblur(username): # 模糊查询 可能会查询到 多个 返回数组
    return User.query.filter(User.username.like('%' + username + '%')).all()

@user.route('/post', methods=['POST'])
def post():
    token = request.headers.get('Authorization').split()[1]
    sender = get_user(token)
    if sender is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    content = request.form.get('content')
    receiver = get_user_by_id(request.form.get('uuid'))
    icon = request.form.get('icon')
    
    receiver.posts.append({
        "sender": sender.id,
        "timestamp": datetime.now(),
        "content": content
    })
    db.session.commit()
    return jsonify({'message': 'Post successfully'}), 200
    

@user.route('/user/search', methods=['GET'])
def search_user():
    type = request.form.get('type')
    if type == 1:
        uuid = request.form.get('input')
        user = get_user_by_id(uuid)
        if user is None:
            return jsonify({'msg': 'User not found'}), 404
        return jsonify([{'uuid': user.id, 
                        'username': user.username,
                        'icon' : user.icon,
                        'intro' : user.intro,
                        'rate' : user.rate,
                        'email' : user.email,
                        }])
        
    elif type == 2:
        username = request.form.get('input')
        users = get_user_by_username_deblur(username)
        if users is None:
            return jsonify({'msg': 'User not found'}), 404
        result = []
        for user in users:
            result.append({'uuid': user.id, 
                            'username': user.username,
                            'icon' : user.icon,
                            'intro' : user.intro,
                            'rate' : user.rate,
                            'email' : user.email,
                            })
        return jsonify(result)


@user.route('/user/<userid>', methods=['GET'])
def get_user_detail(userid):
    """
    TBD
    """
    pass


@user.route('/evaluate_user/<uuid>', methods=['POST'])
def evaluate_user(uuid):
    user = get_user_by_id(uuid)
    if user is None:
        return jsonify({'msg': 'User not found'}), 404
    rate = request.form.get('rate')
    user.rate.append(rate)
    return jsonify({'msg': 'Rate successfully'}), 200


@user.route('/conversation/<uuid>', methods=['GET'])
def conversation(uuid):
    """
    TBD
    """
    pass


@user.route('/send_message', methods=['POST'])
def send_message():
    """
    TBD
    """
    pass


@user.route('/get_history/<uuid>', methods=['GET'])
def get_history(uuid):
    """
    TBD
    """
    pass
