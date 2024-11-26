import time
import traceback
from datetime import datetime
from flask import request, Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from app.models import db, Bot, User, Comment, Chat
from app.routes.auth import get_user
from sqlalchemy import func

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

    bots = (
        db.session.query(Bot, func.count(Chat.id).label('chat_count'))
        .join(Chat, isouter=True)
        .group_by(Bot.id)
        .order_by(func.count(Chat.id).desc())
        .all()
    )

    bots_list = []
    try:
        for bot, chat_count in bots:
            try:
                average_score = Comment.query(func.avg(Comment.score)).scalar()
                total = Comment.query(func.count(Comment.score)).scalar()
            except:
                average_score = 0
                total = 0
            bots_list.append({
                'robotid': bot.id,
                'robot_name': bot.name,
                'base_model': bot.base_model,
                'system_prompt': bot.prompts,
                'knowledge_base': bot.knowledge_base,
                'creator': bot.user_id,
                'quota': bot.quota,
                'price': bot.price,
                'icon': bot.icon,
                'rate': average_score,
                'popularity': total,
                'time': bot.time,
                'is_default': bot.is_default
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
                      base_model=request.form['base_model_id'],
                      prompts=request.form['system_prompt'],
                      price=request.form['price'],
                      icon=request.form['icon'],
                      quota=request.form.get('quota'),
                      knowledge_base=request.form.get('knowledge_base'),
                      is_default=False,
                      rate=None,
                      time=datetime.now()
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
                    'popularity': 0,
                    'rate': 0,
                    'time': new_bot.time,
                    'is_default': new_bot.is_default
                    }), 200


@robots.route('/robot/<robotid>', methods=['GET'])
def get_robot(robotid):
    robot = Bot.query.filter_by(id=robotid).first()
    user = User.query.filter_by(id=robot.user_id).first()
    try:
        average_score = Comment.query.with_entities(func.avg(Comment.score)).scalar()
        total = Comment.query.with_entities(func.count(Comment.score)).scalar()
    except:
        traceback.print_exc()
        average_score = 0
        total = 0
    if robot:
        print(average_score)
        response = {
            "info": {
                "robotid": robot.id,
                "robot_name": robot.name,
                "base_model": robot.base_model,
                "system_prompt": robot.prompts,
                "knowledge_base": robot.knowledge_base,
                "creator": user.username,
                "price": robot.price,
                "quota": robot.quota,
                "icon": robot.icon,
                "rate": average_score,
                "popularity": total,
                'time': robot.time,
                'is_default': robot.is_default
            }
        }
        return jsonify(response), 200
    else:
        return jsonify({"msg": "Robot not found"}), 404


@robots.route('/robot/post/<robotid>', methods=['GET'])
def get_robot_comments(robotid):
    robot = Bot.query.filter_by(id=robotid).first()
    user = User.query.filter_by(id=robot.user_id).first()
    try:
        average_score = Comment.query(func.avg(Comment.score)).scalar()
        total = Comment.query(func.count(Comment.score)).scalar()
    except:
        average_score = 0
        total = 0
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
            "creator": user.id,
            "price": robot.price,
            "quota": robot.quota,
            "icon": robot.icon,
            "rate": average_score,
            "popularity": total,
            "comments": comment_list,
            'time': robot.time
        }

        return jsonify(response), 200
    else:
        return jsonify({"msg": "Robot not found"}), 404


@robots.route('/robot/search', methods=['GET'])
def search_robot():
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    type = int(request.args.get('type'))

    # search by robotid
    if type == 1:
        bot = Bot.query.filter_by(id=int(request.args.get('string'))).first()
        user = User.query.filter_by(id=bot.user_id).first()
        try:
            average_score = Comment.query(func.avg(Comment.score)).scalar()
            total = Comment.query(func.count(Comment.score)).scalar()
        except:
            average_score = 0
            total = 0
        if bot:
            return jsonify({
                'robotid': bot.id,
                'robot_name': bot.name,
                'base_model': bot.base_model,
                'knowledge_base': bot.knowledge_base,
                'creator': bot.user_id,
                'price': bot.price,
                'quota': bot.quota,
                'icon': bot.icon,
                'rate': average_score,
                'popularity': total,
                'time': bot.time
            }), 200
        else:
            return jsonify({"msg": "Robot not found"}), 404
    # search by keywords
    elif type == 2:
        search_string = request.args.get('string', "")
        robots = Bot.query.filter(Bot.name.like(f"%{search_string}%")).all()
        response = []
        try:
            for bot in robots:
                average_score = db.session.query(func.avg(Comment.score)).scalar()
                total = db.session.query(func.count(Comment.score)).scalar()
                response.append({
                    'robotid': bot.id,
                    'robot_name': bot.name,
                    'base_model': bot.base_model,
                    'knowledge_base': bot.knowledge_base,
                    'creator': bot.user_id,
                    'price': bot.price,
                    'quota': bot.quota,
                    'icon': bot.icon,
                    'rate': average_score,
                    'popularity': total,
                    'time': bot.time
                })

            return jsonify(response), 200
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

    try:
        average_score = Comment.query(func.avg(Comment.score)).scalar()
        total = Comment.query(func.count(Comment.score)).scalar()
    except:
        average_score = 0
        total = 0

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
        'popularity': total,
        'rate': average_score,
        'time': bot.time,
        'is_default': bot.is_default
    }), 200


@robots.route('/robot/<robotid>', methods=['DELETE'])
def delete_robot(robotid):
    """
    TBD
    """
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)

    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    robots_info = Bot.query.filter_by(id=robotid).first()

    if robots_info is None:
        return jsonify({'msg': 'Robot not found'}), 404

    if robots_info.user_id != user.id:
        return jsonify({'msg': 'Invalid Credential'}), 401

    db.session.delete(robots_info)
    db.session.commit()

    return jsonify({'msg': 'Chat deleted'}), 200


@robots.route('/robot/post/<robotid>', methods=['POST'])
def post_comment(robotid):
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    has_comment = Comment.query.filter_by(user_id=user.id, bot_id=robotid).all()

    if has_comment is None or len(has_comment) == 0:
        try:
            new_comment = Comment(user_id=user.id,
                                  user_name=user.username,
                                  bot_id=robotid,
                                  content=request.form['content'],
                                  score=request.form['rate'],
                                  time=datetime.now()
                                  )
            db.session.add(new_comment)
            db.session.commit()
            return jsonify({'content': new_comment.content,
                            'score': new_comment.score,
                            'user_name': user.username,
                            'time': new_comment.time}), 200
        except KeyError:
            return jsonify({'msg': 'Missing required fields'}), 400
    else:
        first = has_comment[0]
        first.content = request.form['content']
        first.score = request.form['rate']
        first.time = datetime.now()
        db.session.commit()
        return jsonify({'content': first.content,
                        'score': first.score,
                        'user_name': user.username,
                        'time': first.time}), 200


@robots.route('/selfmodified_robot/<uuid>', methods=['GET'])
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
                'popularity': total,
                'time': bot.time
            })
        return jsonify(bots_list), 200
    except KeyError:
        return jsonify({'msg': 'Missing required fields'}), 400


def get_average_rate(bot_id):
    average_score = Comment.query(func.avg(Comment.score)).scalar()
    total = Comment.query(func.count(Comment.score)).scalar()
    return average_score, total


def calc_timegap(time1, time2):
    if isinstance(time1, str):
        time1 = time.strptime(time1, "%Y-%m-%d %H:%M:%S")
    if isinstance(time2, str):
        time2 = time.strptime(time2, "%Y-%m-%d %H:%M:%S")
    try:
        time1 = datetime(time1[0], time1[1], time1[2])
    except:
        print(time1)
    try:
        time2 = datetime(time2[0], time2[1], time2[2])
    except:
        print(time2)
    print(time1, time2, (time1 - time2).days)
    return (time1 - time2).days


@robots.route('/robot/trendings/<duration>/<type>', methods=['GET'])
# body parameter:
# type: "best-rated most-recent most-viewed"
# duration: recent month all
# recent means within 3 days
def get_robot_trend(duration, type):
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    bots = Bot.query.all()
    bots_score = [{'bot_id': bot.id, 'rate': 0, 'total': 0, 'time': bot.time} for bot in bots]
    timegap = 0  #
    if duration == 'recent':
        timegap = 3
    elif duration == 'month':
        timegap = 30
    elif duration == 'all':
        timegap = 36500

    comments = Comment.query.all()
    for comment in comments:
        time = comment.time
        if calc_timegap(time, datetime.now().strftime("%Y-%m-%d %H:%M:%S")) < timegap:
            for bot in bots_score:
                if bot['bot_id'] == comment.bot_id:
                    bot['rate'] += comment.score
                    bot['total'] += 1

    for bots in bots_score:
        if bots['total'] == 0:
            bots['rate'] = 0
        else:
            bots['rate'] /= bots['total']

    sorted_bots = []
    if type == 'best-rated':
        sorted_bots = sorted(bots_score, key=lambda x: x['rate'], reverse=True)
    if type == 'most-recent':  # 最新发布的
        sorted_bots = sorted(bots_score, key=lambda x: x['time'], reverse=True)
    if type == 'most-viewed':
        sorted_bots = sorted(bots_score, key=lambda x: x['total'], reverse=True)

    response = []
    for bots in sorted_bots:
        bot = Bot.query.filter_by(id=bots['bot_id']).first()
        user = User.query.filter_by(id=bot.user_id).first()
        if len(response) >= 10:
            break
        response.append({
            'robotid': bot.id,
            'robot_name': bot.name,
            'base_model': bot.base_model,
            'system_prompt': bot.prompts,
            'knowledge_base': bot.knowledge_base,
            'creator': user.username,
            'price': bot.price,
            'quota': bot.quota,
            'icon': bot.icon,
            'rate': bots['rate'],
            'popularity': bots['total'],
            'time': bot.time
        })

    return jsonify(response), 200
