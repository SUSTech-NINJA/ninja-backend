import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from flask import Blueprint, request, jsonify
from sqlalchemy.orm.attributes import flag_modified

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

    postid = str(uuid.uuid4())[:8]
    receiver.posts.append({
        "postid": postid,
        "sender": str(sender.id),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": content,
        "responses": [],
    })

    send_email(
        receiver.email,
        f"用户 {sender.username} 在您的主页上发布了新的帖子：<br><br>{content}<br><br>您可以前往您的主页查看详情。:)",
        '[NINJA Chat] 您有新的帖子'
    )

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
            post['responses'].append({
                "postid": postid,
                "sender": str(sender.id),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "icon": sender.icon,
                "content": content
            })
            flag_modified(receiver, 'posts')
            db.session.commit()
            return jsonify({'message': 'Response successfully'}), 200

    return jsonify({'message': 'Post not found'}), 404


@user.route('/user/search', methods=['GET'])
def search_user():
    type = int(request.args.get('type'))
    if type == 1:
        uuid = request.args.get('input')
        try:
            user = get_user_by_id(uuid)
            if user is None:
                return jsonify({'msg': 'User not found'}), 404

            return jsonify([{
                'uuid': str(user.id),
                'username': user.username,
                'icon': user.icon,
                'intro': user.intro,
                'rate': get_average_rate_user(user),
                'email': user.email,
            }]), 200
        except Exception as e:
            return jsonify({'msg': 'Invalid uuid.'}), 404

    elif type == 2:
        username = request.args.get('input')
        users = get_user_by_username_deblur(username)
        if users is None:
            return jsonify({'msg': 'User not found'}), 404

        result = []
        for user in users:
            result.append({
                'uuid': str(user.id),
                'username': user.username,
                'icon': user.icon,
                'intro': user.intro,
                'rate': get_average_rate_user(user),
                'email': user.email,
            })
        return jsonify(result), 200


@user.route('/user/<userid>', methods=['GET'])
def get_user_detail(userid):
    user = get_user_by_id(userid)
    token = request.headers.get('Authorization').split()[1]
    token_user = get_user(token)
    if user is None:
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
    for _, post in enumerate(Post):
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
    token = request.headers.get('Authorization').split()[1]
    sender = get_user(token)
    if sender is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    send_email(user.email, f"用户名为 {sender.username} 的用户对您进行了评价，评分为 {rate} 分。", '您有新的评价')
    try:
        user.rate = user.rate + [int(rate)]
    except:
        return jsonify({'msg': 'Invalid rate'}), 400

    db.session.commit()
    return jsonify({'msg': 'Rate successfully'}), 200


@user.route('/conversation', methods=['GET'])  # 获取私聊列表
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
            'username': get_user_by_id(query['sender']).username
        })
    return jsonify(conversation_list), 200


@user.route('/send_message', methods=['POST'])
def send_message():
    token = request.headers.get('Authorization').split()[1]
    sender = get_user(token)
    if sender is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    content = str(request.form.get('content'))
    receiver = User.query.filter_by(id=request.form.get('uuid')).first()
    flag1 = True
    send_email(receiver.email, f"用户名为 {sender.username} 的用户给您发送了一条消息：\n{content}", '您有新的消息')
    for query in sender.queries:
        if query['sender'] == str(receiver.id):
            flag1 = False
            query['content'].append({
                'sender': str(sender.id),
                'content': content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            flag_modified(sender, 'queries')
            db.session.commit()

    if flag1:
        sender.queries.append({
            'sender': str(receiver.id),
            'content': [
                {
                    'sender': str(sender.id),
                    'content': content,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }]
        })
        db.session.commit()

    flag2 = True
    for query in receiver.queries:
        if query['sender'] == str(sender.id):
            flag2 = False
            query['content'].append({
                'sender': str(sender.id),
                'content': content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            flag_modified(receiver, 'queries')
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


def get_user_by_username_deblur(username):  # 模糊查询 可能会查询到 多个 返回数组
    return User.query.filter(User.username.like('%' + username + '%')).all()


def get_robot_by_uuid(uuid):  # 返回所有该用户创建的机器人
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


def send_email(to_email: str, body: str, subject: str) -> None:
    """
    发送一封固定主题的测试邮件到指定的QQ邮箱。

    参数:
        to_email (str): 收件人的QQ邮箱地址。
        body (str): 邮件的内容。
        subject (str): 邮件的主题。

    返回:
        None
    """
    sender_email = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    smtp_server = 'smtphz.qiye.163.com'
    smtp_port = '465'
    msg = MIMEText(body, 'html', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = f'NINJA Chat <{sender_email}>'
    msg['To'] = to_email
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, [to_email], msg.as_string())
    except smtplib.SMTPException as e:
        print(f'邮件发送失败: {e}')
