import threading
import praw
from abc import ABCMeta, abstractmethod
from collections import namedtuple

from config import bot_config
from config import getLogger


logger = getLogger()  # you will need this to use logger functions
BotSignature = namedtuple('BotSignature', 'classname username permissions')

DEFAULT_SLEEP_INTERVAL = bot_config.get_sleep_interval('default')
RUN_BOTS_ONCE = bot_config.should_run_once()


# region EXCEPTIONS
class MissingRefreshTokenError(ValueError):
    pass


class InvalidBotClassName(ValueError):
    pass
# endregion


# region BASECLASSES
class Bot(threading.Thread, metaclass=ABCMeta):
    """
    Base class for all bots.
    It is a Thread that will continue to do work until it is told to stop.
    """
    def __init__(self, reset_sleep_interval=True, run_once=False, *args, **kwargs):
        """
        :param reset_sleep_interval: If True, the sleep interval will reset to the default value at the beginning of
                                     every loop (you can modify the sleep interval with self.sleep_interval).
                                     It is recommended you leave this True.
        :param run_once: If True, the bot will not repeat its work function and will terminate after running once.
        :param args: Needed so that arbitrary arguments may be passed without raising an exception
        :param kwargs: Needed so that arbitrary keyword arguments may be passed without raising an exception
        """
        super(Bot, self).__init__(daemon=True)
        self.stop_event = threading.Event()
        self.sleep_interval = bot_config.get_sleep_interval(self.__class__.__name__)
        self._reset_sleep_interval = reset_sleep_interval
        self._run_once = RUN_BOTS_ONCE or run_once

    @abstractmethod
    def work(self):
        """
        The method that is called repeatedly in the bot's run loop.
        This is an abstract method, meaning all subclasses of Bot
        must implement their own versions of this method.
        """
        pass

    def run(self):
        """
        An override of Thread.run().
        This is called automatically when the thread's start()
        method is invoked. This function repeatedly calls self.work()
        until something tells it to stop.
        """
        while not self.stop_event.is_set():
            if self._reset_sleep_interval:
                self.sleep_interval = bot_config.get_sleep_interval(self.__class__.__name__)
            self.work()
            if self._run_once:
                self.stop_event.set()
            else:
                self.stop_event.wait(self.sleep_interval)

    def join(self, timeout=None):
        """
        An override of Thread.join().
        Calling join() on a bot will tell it to stop working before closing itself.
        :param timeout: How long the Bot should wait before forcefully closing itself (wait forever if None).
        :return: The original return value of Thread.join()
        """
        self.stop_event.set()
        return super(Bot, self).join(timeout)


class RedditBot(Bot):
    """
    A bot used for working with Reddit via praw.
    This bot has a praw.Reddit instance, through which it
    logs into a Reddit user account and communicates with the Reddit API.
    """

    debug_user_agent_template = '/u/{username} prototyping an automated reddit user'

    def __init__(self, user_name, *args, **kwargs):
        """
        Initializes a Reddit bot.
        :param user_agent: A string passed to Reddit that identifies the Bot.
        :param user_name: A Reddit username that the RedditBot will use.
        """
        super(RedditBot, self).__init__(*args, **kwargs)
        self.USER_NAME = user_name
        self.USER_AGENT = bot_config.get_user_agent(self.__class__.__name__).format(username=self.USER_NAME)
        self.subreddits = bot_config.get_subreddits()
        self.r = None  # the praw.Reddit instance

    @abstractmethod
    def work(self):
        """
        Same as Bot.work().
        Because RedditBot once again declares this as abstract,
        RedditBot must be subclassed, and the subclass must implement
        its own work function.
        """
        pass

    @classmethod
    def get_subclasses(cls):
        """
        A helper function that gets all the subclasses of RedditBot.
        """
        for subclass in cls.__subclasses__():
            yield from subclass.get_subclasses()
            yield subclass

    def run(self):
        """
        An override of Bot.run().
        This method first logs into Reddit
        before entering the run loop.
        :return: value of Bot.run()
        """
        self.login()
        return super(RedditBot, self).run()

    def login(self):
        """
        Logs into Reddit by generating a new praw.Reddit instance.
        If one already exists, the existing instance will be used.
        """
        if not self.r:
            self.r = self.get_reddit_instance()

    def get_reddit_instance(self):
        """
        Creates a new praw.Reddit object and attempts to log into
        a Reddit account using access, secret, and refresh tokens
        saved in praw.ini. If a refresh token is not saved for a
        particular account, account_register.py must be run before
        that account can be used for a RedditBot.
        :return: A Reddit instance with an authenticated user.
        """
        logger.info("Logging into Reddit: username=[{}], useragent=[{}]".format(self.USER_NAME, self.USER_AGENT))
        r = praw.Reddit(user_agent=self.USER_AGENT, site_name=self.USER_NAME)
        try:
            current_access_info = r.refresh_access_information()
        except praw.errors.HTTPException:
            raise MissingRefreshTokenError("No oauth refresh token saved. Please run account_register.py.")
        r.set_access_credentials(**current_access_info)
        return r
# endregion


# region EXAMPLECLASSES
class ExampleBot1(RedditBot):
    """
    An example RedditBot to show how simple it is to create new bots.
    Only a constructor and a work function are needed.
    """
    def __init__(self, user_name):
        super(ExampleBot1, self).__init__(user_name)

    def work(self):
        me = self.r.get_me()

        # use logger.info for general messages
        logger.info("ExampleBot1 working...Username: {}  Link karma: {}".format(me.name, me.link_karma))

        # use logger.warning for warning messages
        logger.warning("Something weird happened or might happen.")

        # use logger.error for error messages
        logger.error("An error occurred.")

        # use logger.exception to include the stack trace (error details) in the error message
        try:
            this_wont_work = int("asdf")  # raises a ValueError
            logger.info(this_wont_work)
        except ValueError:
            logger.exception("An exception occurred.")


class ExampleBot2(RedditBot):
    """
    An example RedditBot to show how simple it is to create new bots.
    Only a constructor and a work function are needed.
    """
    def __init__(self, user_name):
        super(ExampleBot2, self).__init__(user_name)

    def work(self):
        me = self.r.get_me()
        logger.info("ExampleBot2 working...Username: {}  Link karma: {}".format(me.name, me.link_karma))
#endregion
