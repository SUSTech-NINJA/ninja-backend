from flask import request, Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from app.models import db, Bot
from app.routes.auth import get_user

robots = Blueprint('robots', __name__)
headers = {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'X-Accel-Buffering': 'no',
}

@robots.route('/robot', methods=['GET'])
def robot_list():
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    bots_data = Bot.query.all()
    try:
        return jsonify([{
            #Todo
            'id': bot.id,
            'name': bot.name,
            'url': bot.url,
            'usage_limit': bot.usage_limit,
            'price': bot.price,
            'prompts': bot.prompts
        } for bot in bots_data])
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
