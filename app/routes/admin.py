from flask import Blueprint, request, jsonify
from sqlalchemy import func

from app.models import Bot, Comment, db
from app.routes.auth import get_user

admin = Blueprint('admin', __name__)

@admin.route('/admin/robot', methods=['GET'])
def default_robot_list():
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
            if not bot.is_default:
                continue
            bots_list.append({
                'robotid': bot.id,
                'name': bot.name,
                'id': bot.base_model,
                'model_tokens_limitation': bot.quota,
                'price': bot.price,
            })
        return jsonify(bots_list), 200
    except KeyError:
        return jsonify({'msg': 'Missing required fields'}), 400

@admin.route('/admin/robot/add', methods=['POST'])
def create_default_robot():
    """
    create a new bot
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    bot = Bot.query.filter_by(name=request.form['base_model_name']).first()
    if bot is not None:
        return jsonify({'msg': 'This Base Model already Exists'}), 401
    try:
        new_bot = Bot(user_id=user.id,
                      name=request.form['base_model_name'],
                      url='1',
                      base_model=request.form['base_model_id'],
                      prompts="",
                      price=request.form['price'],
                      icon=request.form['icon'],
                      quota=request.form['model_tokens_limitation'],
                      knowledge_base="",
                      is_default=True
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

@admin.route('/admin/robot/update/<base_model_id>', methods=['POST'])
def update_robot(base_model_id):
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    bot = Bot.query.filter_by(base_model=base_model_id).first()
    if bot is None:
        return jsonify({'msg': 'Cannot find this Base Model'}), 401

    if bot.user_id != user.id:
        return jsonify({'msg': 'Invalid Operation'}), 401

    try:
        bot.name = request.form['name']
        bot.price = request.form['price']
        bot.icon = request.form.get('icon')
        bot.quota = request.form['model_tokens_limitation']
    except KeyError:
        return jsonify({'msg': 'Missing required fields'}), 400

    db.session.commit()
    return jsonify({'robotid': bot.id,
                    'robot_name': bot.name,
                    'base_model': bot.base_model,
                    'system_prompt': bot.prompts,
                    'creator': bot.user_id,
                    'icon': bot.icon,
                    'knowledge_base': bot.knowledge_base,
                    'price': bot.price,
                    'quota': bot.quota,
                    'population': None,
                    'rate': None})

@admin.route('/admin/robot/update/<base_model_id>', methods=['DELETE'])
def delete_robot(base_model_id):
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    bot = Bot.query.filter_by(base_model=base_model_id).first()
    if bot is None:
        return jsonify({'msg': 'Cannot find this Base Model'}), 401

    if bot.user_id != user.id:
        return jsonify({'msg': 'Invalid Operation'}), 401

    try:
        db.session.delete(bot)
    except KeyError:
        return jsonify({'msg': 'Deletion failed'}), 400

    db.session.commit()
    return jsonify({'msg': 'Success'})