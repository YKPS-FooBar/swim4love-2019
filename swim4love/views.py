from pathlib import Path

from flask import request, render_template, jsonify, send_from_directory
from flask_socketio import emit

from swim4love import app, db, socketio
from swim4love.models import Swimmer
from swim4love.helper import is_valid_id
from swim4love.site_config import *



##################### AJAX APIs #####################

@app.route('/swimmer/avatar/<swimmer_id>')
def get_swimmer_avatar(swimmer_id):
    # Validation
    if not is_valid_id(swimmer_id):
        return jsonify({'code': 1, 'msg': 'Invalid swimmer ID'}), 400
    swimmer = Swimmer.query.get(int(swimmer_id))
    if not swimmer:
        return jsonify({'code': 3, 'msg': 'Swimmer does not exist'}), 404

    avatar_file = '{}.jpg'.format(swimmer_id)
    if Path('{}/{}/{}'.format(ROOT_DIR, AVATAR_DIR, avatar_file)).is_file():
        return send_from_directory(AVATAR_DIR, avatar_file)
    else:
        return send_from_directory(AVATAR_DIR, DEFAULT_AVATAR)


@app.route('/swimmer/info/<swimmer_id>')
def get_swimmer_info(swimmer_id):
    # Validation
    if not is_valid_id(swimmer_id):
        return jsonify({'code': 1, 'msg': 'Invalid swimmer ID'}), 400
    swimmer = Swimmer.query.get(int(swimmer_id))
    if not swimmer:
        return jsonify({'code': 3, 'msg': 'Swimmer does not exist'}), 404

    # Fetch swimmer information
    data = {'id': swimmer.id, 'name': swimmer.name, 'laps': swimmer.laps}

    return jsonify({'code': 0, 'msg': 'Success', 'data': data})


@app.route('/swimmer/add-lap', methods=['POST'])
def swimmer_add_lap():
    swimmer_id = request.form.get('id')

    # Validate form data
    if not is_valid_id(swimmer_id):
        return jsonify({'code': 1, 'msg': 'Invalid swimmer ID'}), 400
    swimmer = Swimmer.query.get(int(swimmer_id))
    if not swimmer:
        return jsonify({'code': 3, 'msg': 'Swimmer does not exist'}), 404

    # Increment swimmer lap count
    swimmer.laps += 1
    db.session.commit()

    return jsonify({'code': 0, 'msg': 'Success'})


@app.route('/swimmer/add', methods=['POST'])
def add_new_swimmer():
    swimmer_id = request.form.get('id')
    swimmer_name = request.form.get('name')
    swimmer_avatar = request.files.get('avatar')

    # Validate form data
    if not swimmer_id or not swimmer_name:
        return jsonify({'code': 1, 'msg': 'Missing parameters'}), 400
    if not is_valid_id(swimmer_id):
        return jsonify({'code': 1, 'msg': 'Invalid swimmer ID'}), 400
    # swimmer_id should not be replaced with int(swimmer_id)
    # because it is used later when saving the avatar
    if Swimmer.query.get(int(swimmer_id)):
        return jsonify({'code': 2, 'msg': 'Swimmer ID already exists'}), 409

    # Add swimmer into database
    swimmer = Swimmer(id=int(swimmer_id), name=swimmer_name, laps=0)
    db.session.add(swimmer)
    db.session.commit()

    # Save swimmer avatar file
    if swimmer_avatar:
        swimmer_avatar.save('{}/{}/{}.jpg'.format(ROOT_DIR, AVATAR_DIR, swimmer_id))

    return jsonify({'code': 0, 'msg': 'Success'})


##################### SocketIO #####################

@socketio.on('connect')
def socketio_new_connection():
    app.logger.info('New leaderboard connection')
    try:
        emit('init', swimmers_data, json=True)
    except Exception as e:
        app.logger.error(str(e))



##################### Web Pages #####################

@app.route('/leaderboard')
def leaderboard_page():
    return render_template('leaderboard.html')


@app.route('/volunteer')
def volunteer_page():
    return render_template('volunteer.html')


@app.route('/achievement/<swimmer_id>')
def achievement_page(swimmer_id):
    return f'{swimmer_id} achievement not implemented', 404


@app.route('/certificate/<swimmer_id>')
def certificate_page(swimmer_id):
    return f'{swimmer_id} certificate not implemented', 404
