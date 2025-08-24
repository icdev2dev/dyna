from flask import jsonify
from logic.agents_logic import list_agent_configs

def list_agents_endpoint():
    return jsonify(list_agent_configs())
