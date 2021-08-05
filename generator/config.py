import os
import json
import os.path

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

configuration = {}

def load_json_file(path):
    if os.path.isfile(path):
        with open(path, 'r') as config_file:
            return json.load(config_file)
    else:
        return {}


def merge_configurations(base_config: dict, specified_config: dict) -> dict:
    merged_config = {}

    for key, value in base_config.items():
        if isinstance(value, dict):
            merged_config[key] = merge_configurations(value, specified_config.get(key, {}))
        else:
            setting = value
            if key in specified_config:
                setting = specified_config[key]
            merged_config[key] = setting
    
    return merged_config


def get_config(directory):
    global configuration
    
    if not configuration:
        base_configuration = load_json_file(os.path.join(SCRIPT_DIR, "config.json"))
        config_file_path = os.path.join(directory, "statwebgen.json")
        site_configuration = load_json_file(config_file_path)
        configuration = merge_configurations(base_configuration, site_configuration)
        return configuration
    else:
        return configuration