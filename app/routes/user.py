from flask import Blueprint, request, jsonify
from app.models import db, User, Bot  # 确保正确导入你的 User 和 Bot 模型
from datetime import datetime
from app.routes.auth import get_user
from app.models import User, Bot
import uuid


user = Blueprint('user', __name__)


@user.route('/post', methods=['POST'])
def post():
    token = request.headers.get('Authorization').split()[1]
    sender = get_user(token)
    if sender is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    content = request.form.get('content')
    receiver = get_user_by_id(request.form.get('uuid'))

    # 生成一个8位随机数
    postid = str(uuid.uuid4())[:8]
    receiver.posts.append({
        "postid": postid,
        "sender": str(sender.id),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": content,
        "responses": [],
    })
    db.session.commit()
    return jsonify({'message': 'Post successfully'}), 200


@user.route('/response', methods=['POST'])
def response():
    token = request.headers.get('Authorization').split()[1]
    sender = get_user(token)
    if sender is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    content = request.form.get('content')
    postid = request.form.get('postid')
    receiver = get_user_by_id(request.form.get('uuid'))

    response = jsonify({
        "postid": postid,
        "sender": str(sender.id),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "icon": sender.icon,
        "content": content,
    })

    for post in receiver.posts:
        if post['postid'] == postid:
            post['responses'].append(response)
            db.session.commit()
            return jsonify({'message': 'Response successfully'}), 200

    return jsonify({'message': 'Post not found'}), 404


@user.route('/user/search', methods=['GET'])
def search_user():
    type = int(request.form.get('type'))
    if type == 1:
        uuid = request.form.get('input')
        user = get_user_by_id(uuid)
        if user is None:
            return jsonify({'msg': 'User not found'}), 404

        return jsonify([{
            'uuid': str(user.id), 
            'username': user.username,
            'icon' : user.icon,
            'intro' : user.intro,
            'rate': get_average_rate_user(user),
            'email' : user.email,
        }])

    elif type == 2:
        username = request.form.get('input')
        users = get_user_by_username_deblur(username)
        if users is None:
            return jsonify({'msg': 'User not found'}), 404

        result = []
        for user in users:
            result.append({
                'uuid': str(user.id), 
                'username': user.username,
                'icon' : user.icon,
                'intro' : user.intro,
                'rate': get_average_rate_user(user),
                'email' : user.email,
            })
        return jsonify(result)


@user.route('/user/<userid>', methods=['GET'])
def get_user_detail(userid):
    user = get_user_by_id(userid)
    token = request.headers.get('Authorization').split()[1]
    token_user = get_user(token)
    if user is None or not token_user.admin:
        return jsonify({'msg': 'User not found'}), 404

    UserInfo = {
        'uuid': user.id,
        'name': user.username,
        'icon': user.icon,
        'intro': user.intro,
        'rate': get_average_rate_user(user),
        'email': user.email
    }

    Bot = get_robot_by_uuid(userid)
    BotInfo = []
    for bot in Bot:
        print(bot.rate)
        BotInfo.append({
            'robotid': bot.id,
            'robot_name': bot.name,
            'base_model': bot.base_model,
            'system_prompt': bot.prompts,
            'knowledge_base': bot.knowledge_base,
            'creater': userid,
            'price': bot.price,
            'quota': bot.quota,
            'icon': bot.icon,
            'rate': get_average_rate_model(bot),
            'popularity': 0 if bot.rate is None else len(bot.rate),
        })
    PostInfo = []
    Post = user.posts
    for id, post in enumerate(Post):
        PostInfo.append({
            'postid': post['postid'],
            'userid': post['sender'],
            'username': get_user_by_id(post['sender']).username,
            'time': post['timestamp'],
            'content': post['content'],
            'responses': post['responses'],
            'rate': 0, 
            'type': 'post',
            'icon': get_user_by_id(post['sender']).icon
        })
    return jsonify({'UserInfo': UserInfo, 'robot': BotInfo, 'post': PostInfo})


@user.route('/evaluate_user/<uuid>', methods=['POST'])
def evaluate_user(uuid):
    user = get_user_by_id(uuid)
    if user is None:
        return jsonify({'msg': 'User not found'}), 404

    rate = request.form.get('rate')
    try:
        user.rate = user.rate + [int(rate)]
    except:
        return jsonify({'msg': 'Invalid rate'}), 400

    db.session.commit()
    return jsonify({'msg': 'Rate successfully'}), 200


@user.route('/conversation', methods=['GET']) # 获取私聊列表
def conversation():
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'User not found'}), 404

    conversation_list = []
    for query in user.queries:
        conversation_list.append({
            'uuid': query['sender'],
            'icon': get_user_by_id(query['sender']).icon,
            'username': get_user_by_id(query['sender']).username,
        })
    return jsonify(conversation_list), 200


@user.route('/send_message', methods=['POST'])
def send_message():
    token = request.headers.get('Authorization').split()[1]
    sender = get_user(token)
    if sender is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    content = request.form.get('content')
    receiver = get_user_by_id(request.form.get('uuid'))
    flag1 = True

    for query in sender.queries:
        if query.sender == receiver.id:
            flag1 = False
            query.content.append({
                'sender': str(sender.id),
                'content': content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            db.session.commit()

    if flag1:
        sender.queries.append({
            'sender': str(receiver.id),
            'content': [
                {
                    'sender': str(sender.id), 
                    'content': content,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            ]
        })

        db.session.commit()

    flag2 = True
    for query in receiver.queries:
        if query.sender == sender.id:
            flag2 = False
            query.content.append({
                'sender': str(sender.id), 
                'content': content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            db.session.commit()

    if flag2:
        receiver.queries.append({
            'sender': str(sender.id), 
            'content': [
                {
                    'sender': str(sender.id),
                    'content': content,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            ]
        })
        db.session.commit()

    print(get_user_by_id(request.form.get('uuid')).queries)
    print(get_user(token).queries)

    return jsonify({'msg': 'Send successfully'}), 200


@user.route('/get_history/<userid>', methods=['GET'])
def get_history(userid):
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    print(user.queries)
    opponent = get_user_by_id(userid)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    if opponent is None:
        return jsonify({'msg': 'User not found'}), 404

    history = []
    for query in user.queries:
        if query['sender'] == str(opponent.id):
            for content in query['content']:
                history.append({
                    'sender': content['sender'],
                    'icon': get_user_by_id(content['sender']).icon,
                    'content': content['content'],
                })
    return jsonify(history), 200


@user.route('/update/<userid>', methods=['POST'])
def update(userid):
    token = request.headers.get('Authorization').split()[1]
    token_user = get_user(token)

    user = token_user.admin and get_user_by_id(userid) or token_user
    if user is None:
        return jsonify({'msg': 'User not found'}), 404

    user.username = request.form.get('username') is not None and request.form.get('username') or user.username
    user.email = request.form.get('email') is not None and request.form.get('email') or user.email
    user.intro = request.form.get('intro') is not None and request.form.get('intro') or user.intro
    user.icon = request.form.get('icon') is not None and request.form.get('icon') or user.icon
    db.session.commit()
    return jsonify({'msg': 'Update successfully'}), 200


# Utility Functions
def get_user_by_id(uuid):
    return User.query.filter_by(id=uuid).first()

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

def get_user_by_username_deblur(username): # 模糊查询 可能会查询到 多个 返回数组
    return User.query.filter(User.username.like('%' + username + '%')).all()

def get_robot_by_uuid(uuid): # 返回所有该用户创建的机器人
    return Bot.query.filter_by(user_id=uuid).all()

def get_average_rate_model(model):
    rate = model.rate
    if rate is None:
        return 0
    if len(rate) == 0:
        return 0
    sum = 0
    for i in rate:
        sum += i
    return sum / len(rate)

def get_average_rate_user(user):
    rate = user.rate
    if rate is None:
        return 0
    if len(rate) == 0:
        return 0
    sum = 0
    for i in rate:
        sum += i
    return sum / len(rate)
