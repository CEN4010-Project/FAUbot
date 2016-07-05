import yaml
import os
from config import config_directory

bot_config_path = os.path.join(config_directory, "bot_config.yaml")
with open(bot_config_path, "r") as ifile:
    CONFIG = yaml.load(ifile)
