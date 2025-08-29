from flask import jsonify
from flask import Flask, request

from logic.agents_logic import list_agent_configs
from store.sessions import list_sessions_for_agent as store_list_sessions_for_agent, get_last_step_for_session_id as store_get_last_step_for_session_id
from store.sessions import get_agent_id_for_session_id

from queue_imp import stop_agent as store_stop_agent, agent_create as store_create_agent
from queue_imp import agent_pause_action as store_pause_agent, agent_resume_action as store_resume_agent
from queue_imp import agent_interrupt_action as store_interrupt_agent

def list_agents_endpoint():
    return jsonify(list_agent_configs())

def list_sessions_for_agent():

    agent_id = request.args.get('agent_id')

    return jsonify(store_list_sessions_for_agent(agent_id=agent_id))



def create_agent() :
    all_json = request.get_json(silent=True)
    
    agent_id = all_json['agent_id']
    initial_subject = all_json['input']

    store_create_agent(agent_id=agent_id, actor="user", initial_subject=initial_subject)
    return jsonify("ok")

def stop_agent():

    session_id = request.get_json(silent=True)

    retVal= store_stop_agent(session_id=session_id)
    return jsonify(retVal)

def pause_agent():

    session_id = request.get_json(silent=True)

    agent_id = get_agent_id_for_session_id(session_id=session_id)

    retVal = store_pause_agent(agent_id=agent_id, session_id=session_id, actor="user")
    return jsonify(retVal)

def resume_agent():

    session_id = request.get_json(silent=True)

    agent_id = get_agent_id_for_session_id(session_id=session_id)

    retVal = store_resume_agent(agent_id=agent_id, session_id=session_id)
    return jsonify(retVal)

def interrupt_agent():

    all_json = request.get_json(silent=True)
    print(all_json)
    session_id = all_json['session_id']
    guidance = all_json['guidance']

    agent_id = get_agent_id_for_session_id(session_id=session_id)

    retVal = store_interrupt_agent(agent_id=agent_id, session_id=session_id, guidance=guidance )
    return jsonify(retVal)


def get_last_step_for_session_id(): 
    session_id = request.args.get('session_id')
    return (jsonify(store_get_last_step_for_session_id(session_id=session_id)))

