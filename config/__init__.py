from logging import getLogger
from logging.config import fileConfig
import os
import configparser

config_directory = os.path.dirname(__file__)
root = os.path.dirname(config_directory)
log_directory = os.path.join(root, 'logs')
log_file_name = os.path.join(log_directory, "botlog.log")

if not os.path.exists(log_directory):
    os.mkdir(log_directory)

if not os.path.exists(log_file_name):
    with open(log_file_name, "a"):
        pass

log_config_file_name = os.path.join(config_directory, "log_config.ini")
cp = configparser.ConfigParser()
cp.read(log_config_file_name)
new_args = "('{}','midnight',-1,7)".format(log_file_name)

if os.path.sep == "\\":
    new_args = new_args.replace("\\", "\\\\")

cp['handler_file_handler']['args'] = new_args
with open(log_config_file_name, "w") as config_file:
    cp.write(config_file)

fileConfig(os.path.join(config_directory, "log_config.ini"))
