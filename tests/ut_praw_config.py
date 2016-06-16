import os
import unittest
from unittest.mock import patch
from ddt import ddt, unpack, data
from config import praw_config
patch.object = patch.object


TEST_PATH = os.path.dirname(os.path.abspath(__file__))
TEST_CONFIG_PATH = os.path.join(TEST_PATH, "praw_test.ini")


def get_test_parser():
    parser = praw_config.configparser.ConfigParser()
    parser.read(TEST_CONFIG_PATH)
    return parser


@ddt
class PrawConfigTest(unittest.TestCase):

    parser = get_test_parser()
    test_site = "TestSiteName"

    @data((test_site, "first", None, "0"),
          (test_site, "first", parser, "0"),
          (test_site, "second", None, "yes no yes"),
          (test_site, "second", parser, "yes no yes"),
          (test_site, "fourth", None, ""),
          (test_site, "fourth", parser, ""),
          (test_site, "badkey", None, praw_config.InvalidConfigKey),
          ("badsite", "first", None, praw_config.InvalidSiteName))
    @unpack
    def test_get_value(self, site_name, key, current_parser, expected_output):
        with patch.object(praw_config, '_get_parser', return_value=PrawConfigTest.parser):
            if expected_output in (praw_config.InvalidConfigKey, praw_config.InvalidSiteName):
                with self.assertRaises(expected_output):
                    praw_config.get_value(site_name, key, current_parser)
            else:
                result = praw_config.get_value(site_name, key, current_parser)
                self.assertEqual(result, expected_output)

    @data((test_site, "first", "newvalue", None, "newvalue"))
    @unpack
    def test_set_value(self, site_name, key, value, current_parser, expected_output):
        with patch.object(praw_config, '_get_parser', return_value=PrawConfigTest.parser):
            praw_config.set_value(site_name, key, value, current_parser)
            result = praw_config.get_value(site_name, key, current_parser)
            self.assertEqual(result, expected_output)
