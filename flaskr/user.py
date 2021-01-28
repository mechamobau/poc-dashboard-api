from flask import Blueprint, flash, g, request, jsonify
from flaskr.db import get_db
from werkzeug.security import check_password_hash, generate_password_hash
from sqlite3 import Error as SQLiteError
from jwt import DecodeError, encode as jwt_encode, decode as jwt_decode
from functools import wraps

valid_body_keys = ("username", "password", "confirm_password")

def user_by_username(username):
    """Helper function that returns a user based in their username. If user not exists will return none"""

    db = get_db()

    user = db.execute(
        'SELECT id, username, password FROM user WHERE username = ?', (username,)
        ).fetchone()
    return user


def token_required(app):
    def token_required_decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authentication')

            if not token:
                return jsonify({'message': 'token is missing on request', 'data': []}), 401
            
            try:
                data = jwt_decode(token, app.config['SECRET_KEY'],algorithms="HS256")
                current_user = user_by_username(username=data['username'])
            except DecodeError:
                return jsonify({'message': 'token is invalid or expired', 'data': []}), 401
            
            return f(current_user, *args, **kwargs)
        return decorated
    return token_required_decorator

def construct_blueprint(app):
    bp = Blueprint('user', __name__, url_prefix='/user')

    query_user_by_id = 'SELECT id, username, password FROM user WHERE id = ?'
    message_user_not_found = 'user not found'
    message_unexpected_error = 'that occurred an error during user registration'

    @bp.route('/<int:id>', methods=['PUT'])
    def update_user(id):
        db = get_db()
        request_body = request.get_json()

        if request.is_json and all (k in valid_body_keys[:-1] for k in request_body):
            username, password = request_body['username'], request_body['password']
            
            user = db.execute(
                query_user_by_id, (id,)
            ).fetchone()

            if user is None:
                return jsonify({'message': message_user_not_found}), 404

            if user_by_username(username) is not None:
                return jsonify({'message': 'provided username already registered'}), 409
            
            try:
                db.execute(
                    'UPDATE user SET username = ?, password = ? WHERE id = ?',
                    (username, generate_password_hash(password), id)
                )
                db.commit()
                return jsonify({'message': f'user {username} was successfully updated', 'data': {'id': user['id'], 'username': username}}), 200
            except SQLiteError:
                return jsonify({'message': message_unexpected_error}), 500            

        return jsonify({'message': 'invalid request provided'}), 403

    @bp.route('/<int:id>', methods=['DELETE'])
    @token_required(app)
    def delete_user(id):
        db = get_db()

        user = db.execute(
            query_user_by_id, (id,)
        ).fetchone()

        if user is None:
            return jsonify({'message': message_user_not_found}), 404

        try:
            db.execute('DELETE FROM panel_card WHERE panel_id = (SELECT id FROM panel where user_id = ?)', (id,))
            db.commit()

            db.execute('DELETE FROM panel WHERE user_id = ?', (id,))
            db.commit()

            db.execute('DELETE FROM user WHERE id = ?', (id,))
            db.commit()
            return jsonify({'message': f'user was successfully deleted'}), 200
        except SQLiteError:
            return jsonify({'message': message_unexpected_error}), 500            

    @bp.route('/', methods=['POST'])
    def register_user():
        request_body = request.get_json()

        if request.is_json and all (k in valid_body_keys for k in request_body):
            username, password, confirm_password = request_body['username'], request_body['password'], request_body['confirm_password']
            db = get_db()

            user = user_by_username(username)

            if user is not None:
                return jsonify({'message': 'provided username already exists'}), 409
            
            if password != confirm_password:
                return jsonify({'message': 'provided passwords doesn\'t match'}), 401

            try:
                db.execute(
                    'INSERT INTO user (username, password) VALUES (?, ?)',
                    (username, generate_password_hash(password))
                )
                db.commit()

                newuser = user_by_username(username)

                return jsonify({'message': f'user {username} was successfully registered', 'data': {'id': newuser['id'], 'username': newuser['username']}}), 200
            except SQLiteError:
                return jsonify({'message': message_unexpected_error}), 500        

        return jsonify({'message': 'invalid request provided'}), 403

    @bp.route('/<int:id>', methods=['GET'])
    @token_required(app)
    def get_user(id):
        db = get_db()
        user = db.execute(query_user_by_id, (id,)).fetchone()

        if user is None:
            return jsonify({'message': message_user_not_found}), 404

        return jsonify({'data': {'id': user['id'],'username': user['username']}})
    
    @bp.route('/list', methods=['GET'])
    @token_required(app)
    def list_users():
        db = get_db()
        users = db.execute('SELECT id, username, password FROM user')

        return jsonify({'data': [{
            'id': user['id'],
            'username': user['username']
        } for user in users]})

    return bp