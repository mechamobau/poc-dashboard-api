from flaskr.db import get_db
from flaskr.user import token_required
from flask import request, jsonify, Blueprint
from sqlite3 import Error as SQLiteError

def construct_blueprint(app):

    bp = Blueprint('panel', __name__, url_prefix='/panel')
