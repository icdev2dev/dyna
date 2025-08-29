from flask import  request, jsonify
from logic.form_logic import prompt_to_schema

def prompt_to_schema_endpoint():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400

    result = prompt_to_schema(prompt)

    print(result)
    if not result:
        return jsonify({"error": "invalid response"}), 500
    return jsonify(result), 200
