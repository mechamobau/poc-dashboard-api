from flaskr.db import get_db
from flaskr.user import token_required
from flask import request, jsonify, Blueprint
from sqlite3 import Error as SQLiteError

def construct_blueprint(app):

    bp = Blueprint('panel', __name__, url_prefix='/panel')

    message_invalid_request = "invalid request provided"

    @bp.route("/", methods=["POST"])
    @token_required(app)
    def register_panel(current_user):
        expected_keys = ("name")

        request_body = request.get_json()

        if all (x in expected_keys for x in request_body):
            db = get_db()
            cursor = db.cursor()

            panel_name = request_body["name"]

            if panel_name == "":
                return jsonify({"message": "provided name for panel is empty"}), 409

            try:
                cursor.execute("INSERT INTO panel(name, user_id) VALUES(?, ?)", (panel_name, current_user["id"]))
                db.commit()
                print({'id': cursor.lastrowid, 'name': panel_name, "user_id": current_user["id"]})

                return jsonify({"message": "new panel created successfully", "data": {"id": cursor.lastrowid, "name": panel_name}})
            except SQLiteError:
                return jsonify({"message": "an error occured during register proccess"}), 500
        
        return jsonify({"message": message_invalid_request}), 400

    @bp.route("/", methods=["GET"])
    @token_required(app)
    def get_panels(current_user):
        try:
            db = get_db()

            user_id = str(current_user["id"])

            panels = db.execute('SELECT id, name FROM panel WHERE user_id = ?', (user_id,)).fetchall()

            return jsonify({"data": [{
                "id": panel["id"],
                "name": panel["name"]
            } for panel in panels], "count": len(panels)})
        except SQLiteError:
            return jsonify({"message": "an error occured during panel list"}), 500

    @bp.route("<int:panel_id>/cards")
    @token_required(app)
    def get_panel_cards(current_user, panel_id):
        try:
            db = get_db()

            user_id = str(current_user["id"])

            panel_cards = db.execute('SELECT pc.id, pc.title, pc.coord_x, pc.coord_y, pc.width, pc.height, pc.panel_id, pc.created FROM panel_card pc INNER JOIN panel p ON p.id = pc.panel_id WHERE p.id = ?', (panel_id,)).fetchall()

            return jsonify({"data": [{
                "_id": card["id"],
                "title": card["title"],
                "coord_x": card["coord_x"],
                "coord_y": card["coord_y"],
                "width": card["width"],
                "height": card["height"]
            } for card in panel_cards], "count": len(panel_cards)})
        except SQLiteError:
            return jsonify({"message": "an error occured during panel card list"}), 500

    @bp.route("<int:panel_id>/cards", methods=["POST"])
    @token_required(app)
    def register_panel_card(current_user, panel_id):
        db = get_db()

        user_id = str(current_user["id"])

        request_body = request.get_json()

        valid_body_keys = ("title", "coord_x", "coord_y", "width", "height")

        if all (k in valid_body_keys for k in request_body):
            title, coord_x, coord_y, width, height = request_body["title"], request_body["coord_x"], request_body["coord_y"], request_body["width"], request_body["height"]

            try:
                cursor = db.cursor()

                cursor.execute("INSERT INTO panel_card(title, coord_x, coord_y, width, height, panel_id) VALUES (?, ?, ?, ?, ?, ?)", (title, coord_x, coord_y, width, height, panel_id))
                db.commit()

                return jsonify({
                        "message": "the card was successfully registered",
                        "data": {
                            "_id": cursor.lastrowid,
                            "title": title,
                            "coord_x": coord_x,
                            "coord_y": coord_y,
                            "width": width,
                            "height": height
                        }
                    })
            except SQLiteError:
                return jsonify({"message": "an error occured during card register proccess"}), 500
                
        return jsonify({"message": message_invalid_request}), 400

    @bp.route("<int:panel_id>/cards/<int:card_id>", methods=["PUT"])
    @token_required(app)
    def update_panel_card(current_user, panel_id, card_id):
        db = get_db()

        request_body = request.get_json()

        valid_body_keys = ("title", "coord_x", "coord_y", "width", "height")

        if all (k in valid_body_keys for k in request_body):
            title, coord_x, coord_y, width, height = request_body["title"], request_body["coord_x"], request_body["coord_y"], request_body["width"], request_body["height"]

            try:
                cursor = db.cursor()

                cursor.execute("""
                    UPDATE panel_card 
                    SET 
                        title = ?, 
                        coord_x = ?, 
                        coord_y = ?, 
                        width = ?, 
                        height = ? 
                    WHERE panel_id = ?
                    """, (title, coord_x, coord_y, width, height, panel_id))
                db.commit()

                return jsonify({
                        "message": "the card was successfully updated",
                        "data": {
                            "_id": card_id,
                            "title": title,
                            "coord_x": coord_x,
                            "coord_y": coord_y,
                            "width": width,
                            "height": height
                        }
                    }), 202
            except SQLiteError:
                return jsonify({"message": "an error occured during card update proccess"}), 500
                
            
        return jsonify({"message": message_invalid_request}), 400

    @bp.route("<int:panel_id>/cards/<int:card_id>", methods=["DELETE"])
    @token_required(app)
    def delete_panel_card(current_user, panel_id, card_id):
        db = get_db()

        try:
            cursor = db.cursor()

            panel_card = cursor.execute("SELECT * FROM panel_card WHERE panel_id = ? AND id = ?", (panel_id, card_id,)).fetchone()

            if panel_card is None:
                return jsonify({"message": f"the card with id {card_id} don't exist in panel with id {panel_id}!", }), 404

            cursor.execute("DELETE FROM panel_card WHERE panel_id = ? AND id = ?", (panel_id, card_id,))
            db.commit()

            return jsonify({
                    "message": "the card was successfully deleted!",
                    "data": {
                        "_id": panel_card["id"],
                        "title": panel_card["title"],
                        "coord_x": panel_card["coord_x"],
                        "coord_y": panel_card["coord_y"],
                        "width": panel_card["width"],
                        "height": panel_card["height"]
                    }
                }), 202
        except SQLiteError:
            return jsonify({"message": "an error occured during card delete proccess"}), 500

    return bp