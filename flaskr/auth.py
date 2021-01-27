from functools import wraps
from flask import Blueprint, flash, g, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.user import user_by_username
from flaskr.db import get_db
from sqlite3 import Error as SQLiteError
from jwt import DecodeError, encode as jwt_encode, decode as jwt_decode
import datetime

def construct_blueprint(app):
    JWT_EXPIRATION_PERIOD = {'hours': 12}

    bp = Blueprint('auth', __name__, url_prefix='/auth')

    @bp.route('/register', methods=['POST'])
    def register():
        request_body = request.get_json()
        valid_body_keys = ("username", "password", "confirm_password")

        if request.is_json and all (k in valid_body_keys for k in request_body):
            username, password, confirm_password = request_body['username'], request_body['password'], request_body['confirm_password']
            db = get_db()

            user = db.execute('SELECT id FROM user WHERE username = ?', (username,)).fetchone()

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
                return jsonify({'message': f'user {username} was successfully registered'}), 200
            except SQLiteError:
                return jsonify({'message': 'that occurred an error during user registration'}), 500        

        return jsonify({'message': 'invalid request provided'}), 403

    @bp.route('/login', methods=['POST'])
    def authenticate():
        auth = request.authorization

        if not auth or not auth.username or not auth.password:
            return jsonify({'message': 'could not verify', 'WWW-Authenticate': 'Basic auth=\'Login required\''}), 401

        user = user_by_username(auth.username)
        if not user:
            return jsonify({'message': 'user not found', 'data': {}}), 401
        
        if user and check_password_hash(user['password'], auth.password):
            expiration_date = datetime.datetime.now() + datetime.timedelta(**JWT_EXPIRATION_PERIOD)
            token = jwt_encode({'username': user['username'], 'exp': expiration_date}, app.config['SECRET_KEY'])

            return jsonify({'message': 'Validated successfully', 'token': token, 'exp': expiration_date})

        return jsonify({'message': 'could not verify', 'WWW-Authenticate': 'Basic auth=\'Login required\''}), 401

    return bp

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
        