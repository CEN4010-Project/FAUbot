import yaml
import os
from config import config_directory, getLogger

logger = getLogger()

bot_config_path = os.path.join(config_directory, "bot_config.yaml")
with open(bot_config_path, "r") as ifile:
    CONFIG = yaml.load(ifile)


def config_dict_function():
    def outer(fn, *args, **kwargs):
        def key_error_catcher():
            try:
                return fn(*args, **kwargs)
            except KeyError:
                logger.exception("Your bot_config.yaml is missing a section or a key-value pair.")
        return key_error_catcher
    return outer


@config_dict_function()
def get_subreddits():
    return CONFIG['subreddits']


@config_dict_function()
def get_user_agents():
    return CONFIG['user_agents']


def get_user_agent(bot_class_name='debug'):
    return get_user_agents()[bot_class_name]


@config_dict_function()
def get_flags():
    return CONFIG['flags']


def get_flag(flag_name):
    return get_flags()[flag_name]


def should_run_once():
    try:
        return get_flag('should_run_bots_once')
    except KeyError:
        return False


@config_dict_function()
def get_intervals():
    return CONFIG['intervals']


def get_interval(interval_name):
    return get_intervals()[interval_name]

