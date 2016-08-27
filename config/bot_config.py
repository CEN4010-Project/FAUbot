import yaml
import os
from config import config_directory

bot_config_path = os.path.join(config_directory, "bot_config.yaml")
with open(bot_config_path, "r") as ifile:
    CONFIG = yaml.load(ifile)


def get_subreddits():
    return CONFIG['subreddits']


def get_user_agents():
    return CONFIG['user_agents']


def get_user_agent(bot_class_name='debug'):
    return get_user_agents()[bot_class_name]


def get_flags():
    return CONFIG['flags']


def get_flag(flag_name):
    return get_flags()[flag_name]


def should_run_once():
    try:
        return get_flag('should_run_bots_once')
    except KeyError:
        return False


def get_intervals():
    return CONFIG['intervals']


def get_interval(interval_name):
    return get_intervals()[interval_name]


def get_sleep_intervals():
    return get_interval('sleep_intervals')


def get_sleep_interval(bot_class_name='debug'):
    return get_sleep_intervals()[bot_class_name]
