from flask import jsonify
from flask import Flask, request


from store.agent_config import list_agent_configs as store_list_agent_configs
from store.agent_config import upsert_agent_config as store_upsert_agent_config


def list_agent_configs():
    return store_list_agent_configs("all")

def upsert_agent_config():
    all_json = request.get_json(silent=True)
    print(all_json)
    agent_id = all_json['agent_id']
    agent_type = all_json['agent_type']
    agent_description = all_json['agent_description']
    agents_metadata = all_json['agents_metadata']


    return store_upsert_agent_config(
        agent_id=agent_id, 
        agent_description=agent_description,
        agent_type=agent_type, 
        agents_metadata=agents_metadata)


