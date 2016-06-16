import os
import configparser
from enum import IntEnum
CONFIG_PATH = os.path.dirname(os.path.abspath(__file__))
PRAW_FILE_PATH = os.path.join(os.path.dirname(CONFIG_PATH), "praw.ini")
OAUTH_CRED_KEYS = ("oauth_client_id", "oauth_client_secret", "oauth_redirect_uri", "oauth_refresh_token", "oauth_scope")


class CredKeys(IntEnum):
    client, secret, uri, refresh, scope = range(5)


class InvalidConfigKey(ValueError):
    pass


class InvalidSiteName(ValueError):
    pass


class InvalidParser(ValueError):
    pass


def _get_parser(current_parser=None):
    """
    Helper function to reduce the number of duplicate parsers, i.e. number of file reads.
    :param current_parser: Either None, or a config parser object. If None, a new config parser is created.
    :return: Either the current config parser, or a new one.
    """
    if not current_parser:
        current_parser = configparser.ConfigParser()
        current_parser.read(PRAW_FILE_PATH)
    return current_parser


def get_value(site_name, key, _current_parser=None):
    """

    :param site_name:
    :param key:
    :param _current_parser:
    :return:
    """
    parser = _get_parser(_current_parser)
    try:
        site = parser[site_name]
    except KeyError:
        raise InvalidSiteName
    except TypeError:
        raise InvalidParser

    try:
        return site[key]
    except KeyError:
        raise InvalidConfigKey
    except TypeError:
        raise InvalidParser


def _write_config(parser):
    with open(PRAW_FILE_PATH, "w") as c_file:
        parser.write(c_file)


def get_multi_values(site_name, keys, _current_parser=None):
    return {site_name: {key: get_value(site_name, key, _current_parser) for key in keys}}


def set_value(site_name, key, value, _current_parser=None):
    parser = _get_parser(_current_parser)
    parser[site_name][key] = value
    _write_config(parser)


def get_reddit_oath_credentials(site_name, _current_parser=None):
   return get_multi_values(site_name, OAUTH_CRED_KEYS, _current_parser)[site_name]


def set_reddit_oauth_refresh_token(site_name, token, _current_parser=None):
    set_value(site_name, OAUTH_CRED_KEYS[CredKeys.refresh], token, _current_parser)


def get_reddit_oauth_scope(site_name, _current_parser=None):
    return get_value(site_name, OAUTH_CRED_KEYS[CredKeys.scope], _current_parser)


def get_all_site_names(_current_parser=None):
    parser = _get_parser(_current_parser)
    return [site for site in parser if site != "DEFAULT"]


def get_bot_class_name(site_name, _current_parser=None):
    return get_value(site_name, 'bot_class_name', _current_parser)

if __name__ == '__main__':
    print("Config path: {}".format(CONFIG_PATH))
    print("Praw file path: {}".format(PRAW_FILE_PATH))
