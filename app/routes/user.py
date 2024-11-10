from flask import Blueprint, request, jsonify
from app import db  # 确保正确导入你的数据库实例
from app.models import User, Bot  # 确保正确导入你的 User 和 Bot 模型
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.routes.auth import get_user
from app.models import User, Bot
import uuid

user = Blueprint('user', __name__)

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
    if len(rate) == 0:
        return 0
    sum = 0
    for i in rate:
        sum += i
    return sum / len(rate)

def get_average_rate_user(user):
    rate = user.rate
    if len(rate) == 0:
        return 0
    sum = 0
    for i in rate:
        sum += i
    return sum / len(rate)

@user.route('/post', methods=['POST'])
def post():
    token = request.headers.get('Authorization').split()[1]
    sender = get_user(token)
    if sender is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    content = request.form.get('content')
    receiver = get_user_by_id(request.form.get('uuid'))
    icon = request.form.get('icon')
    # 生成一个8位随机数
    postid = str(uuid.uuid4())[:8]
    receiver.posts.append({
        "postid": postid,
        "sender": sender.id,
        "timestamp": datetime.now(),
        "icon": icon,
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
    icon = request.form.get('icon')
    response = jsonify({
        "postid": postid,
        "sender": sender.id,
        "timestamp": datetime.now(),
        "icon": icon,
        "content": content,
    })
    for post in receiver.posts:
        if post.postid == postid:
            post.responses.append(response)
            db.session.commit()
            return jsonify({'message': 'Response successfully'}), 200
    return jsonify({'message': 'Post not found'}), 404
    

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
    user = get_user_by_id(userid)
    if user is None:
        return jsonify({'msg': 'User not found'}), 404
    UserInfo = jsonify({'uuid': user.id,
                        'name': user.username,
                        'icon': user.icon,
                        'intro': user.intro,
                        'rate': get_average_rate_user(user),
                        'email': user.email})
    Bot = get_robot_by_uuid(userid)
    BotInfo = []
    for bot in Bot:
        BotInfo.append(jsonify({'robotid': bot.id,  
                                'robot_name': bot.name,
                                'base_model': bot.base_model,
                                'system_prompt': bot.system_prompt,
                                'knowledge_base': bot.knowledge_base,
                                'creater': userid,
                                'price': bot.price,
                                'quota': bot.quota,
                                'icon': bot.icon,
                                'rate': get_average_rate_model(bot),
                                'popularity': len(bot.rate)
                                }))
    PostInfo = []
    Post = user.posts
    for id, post in enumerate(Post):
        PostInfo.append(jsonify({'postid': post.postid,
                                 'userid': post.sender,
                                 'username': get_user_by_id(post.sender).username,
                                 'time': post.timestamp,
                                 'content': post.content,
                                 'responses': post.responses,
                                 'rate': 0, 
                                 'type': 'post',
                                 'icon': get_user_by_id(post.sender).icon
                                 }))
    PostInfo.append(jsonify({'postid': '',
                             'userid': '',
                             'username': '',
                             'time': '',
                             'content': '',
                             'responses': [],
                             'rate': get_average_rate_user(user),
                             'type': 'rate',
                             'icon': ''
                                }))
    return jsonify({'UserInfo': UserInfo, 'robot': BotInfo, 'post': PostInfo}) 

                                 
@user.route('/evaluate_user/<uuid>', methods=['POST'])
def evaluate_user(uuid):
    user = get_user_by_id(uuid)
    if user is None:
        return jsonify({'msg': 'User not found'}), 404
    rate = request.form.get('rate')
    user.rate.append(rate)
    return jsonify({'msg': 'Rate successfully'}), 200


@user.route('/conversation/<uuid>', methods=['GET']) # 获取私聊列表
def conversation(uuid):
    user = get_user_by_id(uuid)
    if user is None:
        return jsonify({'msg': 'User not found'}), 404
    conversation_list = []
    for query in user.queries:
        conversation_list.append(jsonify({'uuid': query.sender,
                                          'icon': get_user_by_id(query.sender).icon,
                                          'username': get_user_by_id(query.sender).username,
                                          }))
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
            query.content.append({'sender': sender.id, 'content': content})
            db.session.commit()
            return jsonify({'msg': 'Send successfully'}), 200
    if flag1:
        sender.queries.append({'sender': receiver.id, 'content': [{'sender': sender.id, 'content': content}]})
        db.session.commit()
        return jsonify({'msg': 'Send successfully'}), 200
    
    flag2 = True
    for query in receiver.queries:
        if query.sender == sender.id:
            flag2 = False
            query.content.append({'sender': sender.id, 'content': content})
            db.session.commit()
            return jsonify({'msg': 'Send successfully'}), 200
    if flag2:
        receiver.queries.append({'sender': sender.id, 'content': [{'sender': sender.id, 'content': content}]})
        db.session.commit()
        return jsonify({'msg': 'Send successfully'}), 200


@user.route('/get_history/<uuid>', methods=['GET'])
def get_history(uuid):
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    opponent = get_user_by_id(uuid)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    if opponent is None:
        return jsonify({'msg': 'User not found'}), 404
    history = []
    for query in user.queries:
        if query.sender == opponent.id:
            for content in query.content:
                history.append(jsonify({'sender': content.sender,
                                        'icon': get_user_by_id(content.sender).icon,
                                        'content': content.content,
                                        }))
    return jsonify(history), 200
