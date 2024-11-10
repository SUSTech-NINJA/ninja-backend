import time
from datetime import datetime
from flask import request, Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from app.models import db, Bot, User, Comment
from app.routes.auth import get_user
from sqlalchemy import create_engine, func

robots = Blueprint('robots', __name__)
headers = {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'X-Accel-Buffering': 'no',
}


@robots.route('/robot', methods=['GET'])
def robot_list():
    """

    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    bots = Bot.query.all()
    bots_list = []
    try:
        for bot in bots:
            average_score = Comment.query(func.avg(Comment.score)).scalar()
            total = Comment.query(func.count(Comment.score)).scalar()
            bots_list.append({
                'robotid': bot.id,
                'robot_name': bot.name,
                'base_model': bot.base_model,
                'system_prompt': bot.prompts,
                'knowledge_base': bot.knowledge_base,
                'creator': bot.user_id,
                'quota': bot.usage_limit,
                'price': bot.price,
                'icon': bot.icon,
                'rate': average_score,
                'population': total,
            })
        return jsonify(bots_list), 200
    except KeyError:
        return jsonify({'msg': 'Missing required fields'}), 400


@robots.route('/robot/new', methods=['POST'])
def create_robot():
    """
    create a new bot
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    try:
        new_bot = Bot(user_id=user.id,
                      name=request.form['name'],
                      url='1',
                      base_model=request.form['base_model_id'],
                      prompts=request.form['system_prompt'],
                      price=request.form['price'],
                      icon=request.form['icon'],
                      quota=request.form.get('quota'),
                      knowledge_base=request.form.get('knowledge_base')
                      )
    except KeyError:
        return jsonify({'msg': 'Missing required fields'}), 400
    db.session.add(new_bot)
    db.session.commit()
    return jsonify({'robotid': new_bot.id,
                    'robot_name': new_bot.name,
                    'base_model': new_bot.base_model,
                    'system_prompt': new_bot.prompts,
                    'creator': new_bot.user_id,
                    'icon': new_bot.icon,
                    'knowledge_base': new_bot.knowledge_base,
                    'price': new_bot.price,
                    'quota': new_bot.quota,
                    'population': None,
                    'rate': None})


@robots.route('/robot/<robotid>', methods=['GET'])
def get_robot(robotid):
    robot = Bot.query.filter_by(id=robotid).first()
    user = User.query.filter_by(id=robot.user_id).first()
    average_score = Comment.query(func.avg(Comment.score)).scalar()
    total = Comment.query(func.count(Comment.score)).scalar()
    if robot:
        response = {
            "info": {
                "robotid": robot.id,
                "robot_name": robot.name,
                "base_model": robot.base_model,
                "system_prompt": robot.prompts,
                "knowledge_base": robot.knowledge_base,
                "creator": user.name,
                "price": robot.price,
                "quota": robot.quota,
                "icon": robot.icon,
                "rate": average_score,
                "population": total
            }
        }
        return jsonify(response), 200
    else:
        return jsonify({"msg": "Robot not found"}), 404


@robots.route('/robot/post/{robotid}', methods=['GET'])
def get_robot_comments(robotid):
    robot = Bot.query.filter_by(id=robotid).first()
    user = User.query.filter_by(id=robot.user_id).first()
    average_score = Comment.query(func.avg(Comment.score)).scalar()
    total_score = Comment.query(func.sum(Comment.score)).scalar()
    comments = Comment.query.filter_by(bot_id=robotid).all()
    comment_list = [
        {
            "user_name": comment.user_name,
            "text": comment.content,
            "time": comment.time
        } for comment in comments
    ]
    if robot:
        response = {
            "robotid": robot.id,
            "robot_name": robot.name,
            "base_model": robot.base_model,
            "system_prompt": robot.prompts,
            "knowledge_base": robot.knowledge_base,
            "creator": user.name,
            "price": robot.price,
            "quota": robot.quota,
            "icon": robot.icon,
            "rate": average_score,
            "population": total_score,
            "comments": comment_list
        }

        return jsonify(response), 200
    else:
        return jsonify({"msg": "Robot not found"}), 404


@robots.route('/robot/post/{robotid}', methods=['GET'])
def search_robot():
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    type = request.form['type']
    #search by robotid
    if type == 1:
        robot = Bot.query.filter_by(id=int(request.form['input'])).first()
        user = User.query.filter_by(id=robot.user_id).first()
        average_score = Comment.query(func.avg(Comment.score)).scalar()
        total = Comment.query(func.count(Comment.score)).scalar()
        if robot:
            response = {
                "info": {
                    "robotid": robot.id,
                    "robot_name": robot.name,
                    "base_model": robot.base_model,
                    "system_prompt": robot.prompts,
                    "knowledge_base": robot.knowledge_base,
                    "creator": user.name,
                    "price": robot.price,
                    "quota": robot.quota,
                    "icon": robot.icon,
                    "rate": average_score,
                    "population": total
                }
            }
            return jsonify(response), 200
        else:
            return jsonify({"msg": "Robot not found"}), 404
    #search by keywords
    elif type == 2:
        robots = Bot.query.filter_by(Bot.name.like(request.form['input'])).all()
        bots_list = []
        try:
            for bot in robots:
                average_score = Comment.query(func.avg(Comment.score)).scalar()
                total = Comment.query(func.count(Comment.score)).scalar()
                bots_list.append({
                    'robotid': bot.id,
                    'robot_name': bot.name,
                    'base_model': bot.base_model,
                    'system_prompt': bot.prompts,
                    'knowledge_base': bot.knowledge_base,
                    'creator': bot.user_id,
                    'quota': bot.usage_limit,
                    'price': bot.price,
                    'icon': bot.icon,
                    'rate': average_score,
                    'population': total,
                })
            return jsonify(bots_list), 200
        except KeyError:
            return jsonify({'msg': 'Missing required fields'}), 400
    return jsonify({'msg': 'Missing required fields'}), 400


@robots.route('/robot/<robotid>', methods=['POST'])
def update_robot(robotid):
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    bot = Bot.query.filter_by(id=robotid).first()
    if bot is None:
        return jsonify({'msg': 'Bot not found'}), 404

    if bot.user_id != user.id:
        return jsonify({'msg': 'Unauthorized action'}), 403

    try:
        if 'name' in request.form:
            bot.name = request.form['name']
        if 'base_model_id' in request.form:
            bot.base_model = request.form['base_model_id']
        if 'system_prompt' in request.form:
            bot.prompts = request.form['system_prompt']
        if 'price' in request.form:
            bot.price = request.form['price']
        if 'icon' in request.form:
            bot.icon = request.form['icon']
        if 'quota' in request.form:
            bot.quota = request.form['quota']
        if 'knowledge_base' in request.form:
            bot.knowledge_base = request.form['knowledge_base']

    except KeyError:
        return jsonify({'msg': 'Invalid or missing fields'}), 400

    db.session.commit()

    average_score = Comment.query(func.avg(Comment.score)).scalar()
    total = Comment.query(func.count(Comment.score)).scalar()

    return jsonify({
        'robotid': bot.id,
        'robot_name': bot.name,
        'base_model': bot.base_model,
        'system_prompt': bot.prompts,
        'creator': bot.user_id,
        'icon': bot.icon,
        'knowledge_base': bot.knowledge_base,
        'price': bot.price,
        'quota': bot.quota,
        'population': total,
        'rate': average_score
    })


@robots.route('/robot/<robotid>', methods=['DELETE'])
def delete_robot(robotid):
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    robots_info = Bot.query.filter_by(id=robotid)

    if robots_info is None:
        return jsonify({'msg': 'Robot not found'}), 404

    if robots_info.user_id != user.id:
        return jsonify({'msg': 'Invalid Credential'}), 401

    db.session.delete(robots_info)
    db.session.commit()

    return jsonify({'msg': 'Chat deleted'}), 200


@robots.route('/robot/post/{robotid}', methods=['POST'])
def post_comment(robotid):
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    has_comment = Comment.query.filter_by(user_id=user.id).all()

    if has_comment is None:
        try:
            new_comment = Comment(user_id=user.id,
                                  user_name=user.username,
                                  bot_id=robotid,
                                  content=request.form['content'],
                                  score=request.form['rate'],
                                  )
            db.session.add(new_comment)
            db.session.commit()
            return jsonify({'content': new_comment.content,
                            'score': new_comment.score,
                            'user_name': user.username,
                            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}), 200
        except KeyError:
            return jsonify({'msg': 'Missing required fields'}), 400
    else:
        return jsonify({'msg': 'Comment already exists'}), 403


@robots.route('/selfmodified_robot/{uuid}', methods=['GET'])
def selfmodified_robot(uuid):
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    robots = Bot.query.filter_by(user_id=uuid).all()
    bots_list = []
    try:
        for bot in robots:
            average_score = Comment.query(func.avg(Comment.score)).scalar()
            total = Comment.query(func.count(Comment.score)).scalar()
            bots_list.append({
                'robotid': bot.id,
                'robot_name': bot.name,
                'base_model': bot.base_model,
                'system_prompt': bot.prompts,
                'knowledge_base': bot.knowledge_base,
                'creator': bot.user_id,
                'quota': bot.usage_limit,
                'price': bot.price,
                'icon': bot.icon,
                'rate': average_score,
                'population': total,
            })
        return jsonify(bots_list), 200
    except KeyError:
        return jsonify({'msg': 'Missing required fields'}), 400


@robots.route('/robot/trendings', methods=['GET'])
def get_robot_trend():
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    
