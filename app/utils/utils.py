import re
import yaml


def strip_ansi_codes(text):
    ansi_escape = re.compile(r"\x1B\[[0-?9;]*[mK]")
    return ansi_escape.sub("", text)


def load_config_yaml():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)


def save_config_yaml(config):
    with open("config.yaml", "w") as file:
        yaml.dump(config, file)
