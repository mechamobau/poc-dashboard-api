from flask import Blueprint, flash, g, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.user import user_by_username
from flaskr.db import get_db
from sqlite3 import Error as SQLiteError
from jwt import encode as jwt_encode
import datetime

from flaskr.user import valid_body_keys

def construct_blueprint(app):
    JWT_EXPIRATION_PERIOD = {'hours': 12}

    bp = Blueprint('auth', __name__, url_prefix='/auth')

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