from store.agent_config import list_agent_configs as store_list_agent_configs

from queue_imp import agent_destroy_action

def list_agent_configs():
    # Pretend this returns from DB, here is hardcoded for demo:
    return store_list_agent_configs()
