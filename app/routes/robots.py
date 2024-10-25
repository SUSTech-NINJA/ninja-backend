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
                    'knowledge_bale': new_bot.knowledge_base,
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


@robots.route('/robot/<robotid>', methods=['POST'])
def update_robot():
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    bot = Bot.query.filter_by(id=robots).first()
    if bot.user_id != user.id:
        return jsonify({'msg': 'Invalid'}), 401
