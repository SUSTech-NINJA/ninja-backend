from flask import Blueprint, request, jsonify
from app import db  # 确保正确导入你的数据库实例
from app.models import User, Bot  # 确保正确导入你的 User 和 Bot 模型
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import uuid

user = Blueprint('user', __name__)

# Helper Functions

def user_to_userinfo(user_obj):
    """
    将 User 对象转换为 UserInfo 字典。
    """
    settings = user_obj.settings or {}
    # 计算 credit 的平均值
    credit = user_obj.credit or {}
    if isinstance(credit, dict) and credit:
        rate = sum(credit.values()) / len(credit)
    else:
        rate = 0

    user_info = {
        "email": settings.get('email', ""),
        "icon": settings.get('icon', ""),
        "intro": settings.get('intro', ""),
        "name": user_obj.username,
        "rate": rate,
        "uuid": user_obj.id
        # 可以根据需要添加更多字段
    }
    return user_info

def post_to_postentry(post, userid, username):
    """
    将帖子数据转换为 PostEntry 字典。
    """
    return {
        "content": post.get('content', ""),
        "icon": post.get('icon', ""),
        "postid": post.get('postid'),  # 假设每个帖子有唯一的 postid
        "rate": post.get('rate'),  # 可选
        "responses": [post_to_postentry(response, userid, username) for response in post.get('responses', [])],
        "time": post.get('timestamp', ""),
        "type": post.get('type', "post"),  # 默认类型为 'post'
        "userid": userid,
        "username": username
        # 可以根据需要添加更多字段
    }

def bot_to_robot(bot_obj):
    """
    将 Bot 对象转换为 Robot 字典。
    """
    # 计算机器人的平均评分
    # 假设有一个评分系统，这里简化为直接使用 bot_obj.rate
    # 如果评分存储在其他地方，需要根据实际情况修改
    # 这里假设 Bot 模型有一个 'rate' 字段
    # 如果没有，需要从其他来源计算
    return {
        "base_model": bot_obj.base_model,
        "creator": bot_obj.user_id,
        "icon": bot_obj.icon,
        "knowledge_base": bot_obj.knowledge_base,
        "population": bot_obj.population if hasattr(bot_obj, 'population') else 0,  # 需要在 Bot 模型中定义
        "price": bot_obj.price,
        "quota": bot_obj.quota,
        "rate": bot_obj.rate if hasattr(bot_obj, 'rate') else 0,  # 需要在 Bot 模型中定义
        "robot_name": bot_obj.name,
        "robotid": str(bot_obj.id),
        "system_prompt": bot_obj.prompts.get('system_prompt', "") if bot_obj.prompts else ""
        # 可以根据需要添加更多字段
    }

# Existing Routes

@user.route('/settings', methods=['GET', 'POST'])
def settings():
    """
    TBD
    """
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        pass


@user.route('/post', methods=['POST'])
def post():
    """
    创建一个新的帖子。
    请求体参数:
    - content: 发帖的内容 (可选)
    - icon: 发帖人的头像 (可选)
    - name: 被发帖人的用户名 (可选)
    - uuid: 被发帖人的用户ID (可选)
    返回:
    - {"msg": "success"} 成功
    - {"msg": "failure", "error": "错误信息"} 失败
    """
    data = request.get_json()
    if not data:
        return jsonify({"msg": "failure", "error": "无效的请求体"}), 400

    content = data.get('content')
    icon = data.get('icon')
    name = data.get('name')
    uuid_param = data.get('uuid')

    # 验证至少需要一个标识用户的参数
    if not uuid_param and not name:
        return jsonify({"msg": "failure", "error": "缺少用户标识信息（uuid 或 name）"}), 400

    try:
        # 根据 uuid 或 name 查找用户
        if uuid_param:
            user_obj = User.query.filter_by(id=uuid_param).first()
        else:
            user_obj = User.query.filter_by(username=name).first()

        if not user_obj:
            return jsonify({"msg": "failure", "error": "用户未找到"}), 404

        # 创建新的帖子
        new_post = {
            "content": content,
            "icon": icon,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "post",
            "userid": user_obj.id,
            "username": user_obj.username,
            "postid": str(uuid.uuid4()),  # 生成唯一的 postid
            "responses": []
            # 可以根据需要添加更多字段
        }

        # 初始化 posts 字段为列表如果为空
        if not user_obj.posts:
            user_obj.posts = []

        user_obj.posts.append(new_post)

        db.session.commit()
        return jsonify({"msg": "success"}), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"msg": "failure", "error": str(e)}), 500
    except Exception as e:
        return jsonify({"msg": "failure", "error": str(e)}), 500


@user.route('/user/search', methods=['GET'])
def search_user():
    """
    根据输入搜索用户信息。
    查询参数:
    - input: 用户输入的搜索关键字 (可选)
    - type: 搜索类型，1 代表 uuid，2 代表用户名 (可选)
    返回:
    - UserInfo JSON 对象
    """
    input_value = request.args.get('input', '')
    search_type = request.args.get('type', type=int)

    if not input_value:
        return jsonify({"msg": "failure", "error": "缺少搜索输入"}), 400

    if search_type not in [1, 2]:
        return jsonify({"msg": "failure", "error": "无效的搜索类型"}), 400

    try:
        if search_type == 1:
            # 按 uuid 搜索
            user_obj = User.query.filter_by(id=input_value).first()
        elif search_type == 2:
            # 按用户名搜索，使用模糊匹配
            user_obj = User.query.filter(User.username.like(f"%{input_value}%")).first()

        if not user_obj:
            return jsonify({"msg": "failure", "error": "用户未找到"}), 404

        # 计算 credit 的平均值
        credit = user_obj.credit or {}
        if isinstance(credit, dict) and credit:
            rate = sum(credit.values()) / len(credit)
        else:
            rate = 0

        # 构建 UserInfo 响应
        user_info = {
            "email": user_obj.settings.get('email') if user_obj.settings else "",
            "icon": user_obj.settings.get('icon') if user_obj.settings else "",
            "intro": user_obj.settings.get('intro') if user_obj.settings else "",
            "name": user_obj.username,
            "rate": rate,
            "uuid": user_obj.id
            # 可以根据需要添加更多字段
        }

        return jsonify(user_info), 200

    except Exception as e:
        return jsonify({"msg": "failure", "error": str(e)}), 500


@user.route('/user/<userid>', methods=['GET'])
def get_user_detail(userid):
    """
    获取指定用户的详细信息，包括用户信息、帖子和机器人信息。
    路径参数:
    - userid: 用户的 UUID
    返回:
    - {
        "post": [PostEntry],
        "robot": [Robot],
        "UserInfo": UserInfo
      }
    """
    try:
        user_obj = User.query.filter_by(id=userid).first()
        if not user_obj:
            return jsonify({"msg": "failure", "error": "用户未找到"}), 404

        # 获取用户信息
        user_info = user_to_userinfo(user_obj)

        # 获取用户帖子
        posts = user_obj.posts or []
        post_entries = [post_to_postentry(post, user_obj.id, user_obj.username) for post in posts]

        # 获取用户机器人
        bots = Bot.query.filter_by(user_id=userid).all()
        robot_entries = [bot_to_robot(bot) for bot in bots]

        response = {
            "post": post_entries,
            "robot": robot_entries,
            "UserInfo": user_info
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"msg": "failure", "error": str(e)}), 500


@user.route('/evaluate_user/<uuid>', methods=['POST'])
def evaluate_user(uuid):
    """
    对指定用户进行评价，提交评分并更新用户的信用信息。
    路径参数:
    - uuid: 被评价用户的 UUID
    请求体参数:
    - rate: 给用户的评分 (1-5)
    返回:
    - {"msg": "success"} 成功
    - {"msg": "failure", "error": "错误信息"} 失败
    """
    data = request.get_json()
    if not data:
        return jsonify({"msg": "failure", "error": "无效的请求体"}), 400

    rate = data.get('rate')
    if rate is None:
        return jsonify({"msg": "failure", "error": "缺少评分参数"}), 400

    if not isinstance(rate, (int, float)) or not (1 <= rate <= 5):
        return jsonify({"msg": "failure", "error": "评分必须是 1 到 5 之间的数字"}), 400

    try:
        user_obj = User.query.filter_by(id=uuid).first()
        if not user_obj:
            return jsonify({"msg": "failure", "error": "用户未找到"}), 404

        # 更新用户的 credit 字段
        # 假设 credit 是一个字典，键为评价者的 UUID 或其他唯一标识，这里由于没有评价者信息，
        # 我们可以使用当前时间戳或随机 UUID 作为键
        if not user_obj.credit:
            user_obj.credit = {}

        # 生成一个唯一的键，示例使用当前时间戳
        evaluator_id = str(uuidlib.uuid4())
        user_obj.credit[evaluator_id] = rate

        db.session.commit()
        return jsonify({"msg": "success"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"msg": "failure", "error": str(e)}), 500
    except Exception as e:
        return jsonify({"msg": "failure", "error": str(e)}), 500


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
