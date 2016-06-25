from logging import getLogger
from logging.config import fileConfig
import os

config_directory = os.path.dirname(__file__)
root = os.path.dirname(config_directory)
log_directory = os.path.join(root, 'logs')
log_file_name = os.path.join(log_directory, "botlog.log")

if not os.path.exists(log_directory):
    os.mkdir(log_directory)

if not os.path.exists(log_file_name):
    with open(log_file_name, "a"):
        pass


fileConfig(os.path.join(config_directory, "log_config.ini"))
