from flask import jsonify
from flask import Flask, request

from logic.agents_logic import list_agent_configs
from store.sessions import list_sessions_for_agent as store_list_sessions_for_agent

def list_agents_endpoint():
    return jsonify(list_agent_configs())

def list_sessions_for_agent():
    agent_id = request.args.get('agent_id')
    return jsonify(store_list_sessions_for_agent(agent_id=agent_id))
