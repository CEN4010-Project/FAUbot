import yaml
import os
from config import config_directory

bot_config_path = os.path.join(config_directory, "bot_config.yaml")
with open(bot_config_path, "r") as ifile:
    CONFIG = yaml.load(ifile)


def get_user_agent(bot_class_name):
    return CONFIG['user_agents'][bot_class_name]
