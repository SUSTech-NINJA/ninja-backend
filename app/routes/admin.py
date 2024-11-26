import random

from flask import Blueprint, request, jsonify
from sqlalchemy import func
import xlwt
import base64
import io
from datetime import datetime
import os
from app.models import Bot, Comment, db, User, Bill
from app.routes.auth import get_user

admin = Blueprint('admin', __name__)

@admin.route('/admin/robot', methods=['GET'])
def default_robot_list():
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
                'icon': bot.icon
            })
        return jsonify(bots_list), 200
    except KeyError:
        return jsonify({'msg': 'Missing required fields'}), 400

@admin.route('/admin/robot/add', methods=['POST'])
def create_default_robot(): # create a new bot
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
                      base_model=request.form['base_model_id'],
                      prompts="",
                      price=request.form['price'],
                      icon=request.form['icon'],
                      quota=request.form['model_tokens_limitation'],
                      knowledge_base="",
                      is_default=True,
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
                    'time': new_bot.time})

@admin.route('/admin/robot/update/<base_model_id>', methods=['POST'])
def update_robot(base_model_id):
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    print(token,user,base_model_id,request.headers.get('Authorization'))
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    bot = Bot.query.filter_by(base_model=base_model_id).first()
    if bot is None:
        return jsonify({'msg': 'Cannot find this Base Model'}), 401

    if bot.user_id != user.id and not user.admin:
        return jsonify({'msg': 'Invalid Operation'}), 401

    try:
        bot.name = request.form['base_model_name']
        bot.price = request.form['price']
        bot.icon = request.form.get('icon')
        bot.quota = request.form['model_tokens_limitation']
    except KeyError:
        return jsonify({'msg': 'Missing required fields'}), 400

    db.session.commit()

    try:
        average_score = Comment.query(func.avg(Comment.score)).scalar()
        total = Comment.query(func.count(Comment.score)).scalar()
    except:
        average_score = 0
        total = 0

    return jsonify({'robotid': bot.id,
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
                    'time': bot.time
                    })

@admin.route('/admin/robot/update/<base_model_id>', methods=['DELETE'])
def delete_robot(base_model_id):
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401
    bot = Bot.query.filter_by(base_model=base_model_id).first()
    if bot is None:
        return jsonify({'msg': 'Cannot find this Base Model'}), 401

    if bot.user_id != user.id and not user.admin:
        return jsonify({'msg': 'Invalid Operation'}), 401

    try:
        db.session.delete(bot)
    except KeyError:
        return jsonify({'msg': 'Deletion failed'}), 400

    db.session.commit()
    return jsonify({'msg': 'Success'})
 
@admin.route('/admin/export/comment/<robot_id>', methods=['GET'])
def export_comment(robot_id):
    token = request.headers.get('Authorization').split()[1]
    user = get_user(token)
    if user is None:
        return jsonify({'msg': 'Invalid Credential'}), 401

    r = str(random.uniform(1, 10))
    print(robot_id)
    comments = Comment.query.filter_by(bot_id=robot_id).all()
    print(comments)

    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('Comments')

    headers = ['ID', 'User ID', 'User Name', 'Bot ID', 'Score', 'Time']
    for col, header in enumerate(headers):
        sheet.write(0, col, header)

    for row, comment in enumerate(comments, start=1):
        sheet.write(row, 0, comment.id)
        sheet.write(row, 1, str(comment.user_id))
        sheet.write(row, 2, comment.user_name)
        sheet.write(row, 3, comment.bot_id)
        sheet.write(row, 4, comment.score)
        sheet.write(row, 5, comment.time.strftime('%Y-%m-%d %H:%M:%S'))

    # save
    time_str = str(datetime.now())
    workbook.save('comments-'+ r+'.xls')
    with open('comments-'+r+ '.xls', 'rb') as f:
        data = f.read()
        # os.remove('comments-'+r+'.xls')
    return data, 200

@admin.route('/admin/export/summary', methods=['GET'])
def export_summary():
    users = User.query.all()
    bots = Bot.query.all()
    bills = Bill.query.all()
    workbook = xlwt.Workbook()

    # --------- 用户信息工作表 ---------
    user_sheet = workbook.add_sheet('Users')
    user_headers = ['ID', 'Username', 'Admin',  'Current', 'Rate']
    for col, header in enumerate(user_headers):
        user_sheet.write(0, col, header)
    
    for row, user in enumerate(users, start=1):
        user_sheet.write(row, 0, str(user.id))
        user_sheet.write(row, 1, user.username)
        user_sheet.write(row, 2, user.admin)
        user_sheet.write(row, 3, str(user.current))
        user_sheet.write(row, 4, str(user.rate))
    
    total_users = len(users)
    user_sheet.write(len(users) + 1, 0, f'Number of User：{total_users}')

    # --------- 机器人信息工作表 ---------
    bot_sheet = workbook.add_sheet('Bots')
    bot_headers = ['ID', 'User ID', 'Name', 'Base Model', 'Quota', 'Price', 'Prompts', 'Knowledge Base', 'Is Default', 'Rate']
    for col, header in enumerate(bot_headers):
        bot_sheet.write(0, col, header)
    
    for row, bot in enumerate(bots, start=1):
        try:
            average_score = db.session.query(func.avg(Comment.score)).filter(Comment.bot_id == bot.id).scalar()
        except:
            average_score = 0
        bot_sheet.write(row, 0, bot.id)
        bot_sheet.write(row, 1, str(bot.user_id))
        bot_sheet.write(row, 2, bot.name)
        bot_sheet.write(row, 3, bot.base_model)
        bot_sheet.write(row, 4, bot.quota)
        bot_sheet.write(row, 5, bot.price)
        bot_sheet.write(row, 6, str(bot.prompts))
        bot_sheet.write(row, 7, bot.knowledge_base)
        bot_sheet.write(row, 8, bot.is_default)
        bot_sheet.write(row, 9, str(average_score))
    
    total_bots = len(bots)
    bot_sheet.write(len(bots) + 1, 0, f'Number of Bot：{total_bots}')

    # --------- 收益信息工作表 ---------
    bill_sheet = workbook.add_sheet('Bills')
    bill_headers = ['ID', 'User ID', 'Bill']
    for col, header in enumerate(bill_headers):
        bill_sheet.write(0, col, header)
    
    total_margin = 0
    for row, bill in enumerate(bills, start=1):
        bill_sheet.write(row, 0, str(bill.id))
        bill_sheet.write(row, 1, str(bill.user_id))
        bill_sheet.write(row, 2, str(bill.bill))
        total_margin += bill.bill
    bill_sheet.write(len(bills) + 1, 0, f'Total Margin：{total_margin}')

    time_str = str(datetime.now())
    workbook.save('summary-'+ time_str +'.xls')
    with open('summary-'+ time_str +'.xls', 'rb') as f:
        data = f.read()
        os.remove('summary-'+ time_str +'.xls')
    return data, 200


    
    
    
    