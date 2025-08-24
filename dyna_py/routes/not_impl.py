from flask import jsonify

def not_implemented():
    return jsonify({"error": "Not yet implemented"}), 500
