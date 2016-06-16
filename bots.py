import praw
import threading
from time import sleep
from collections import namedtuple
from abc import ABCMeta, abstractmethod

from config import praw_config

BotSignature = namedtuple('BotSignature', 'classname username useragent permissions')


class MissingRefreshTokenError(ValueError):
    pass


class Bot(threading.Thread, metaclass=ABCMeta):
    """
    Base class for all bots.
    It is a Thread that will continue to do work until it is told to stop.
    """
    def __init__(self, user_agent=None, user_name=None, permissions=None, *args, **kwargs):
        super(Bot, self).__init__(daemon=True)
        self.stop = False

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
        while not self.stop:
            self.work()

    def join(self, timeout=None):
        """
        An override of Thread.join().
        Calling join() on a bot will tell it to stop working before closing itself.
        :param timeout: How long the Bot should wait before forcefully closing itself (wait forever if None).
        :return: The original return value of Thread.join()
        """
        self.stop = True
        return super(Bot, self).join(timeout)


class RedditBot(Bot):
    """
    A bot used for working with Reddit via praw.
    This bot has a praw.Reddit instance, through which it
    logs into a Reddit user account and communicates with the Reddit API.
    """

    debug_user_agent_template = '/u/{username} prototyping an automated reddit user'

    def __init__(self, user_agent=None, user_name=None, *args, **kwargs):
        """
        Initializes a Reddit bot.
        :param user_agent: A string passed to Reddit that identifies the Bot.
        :param user_name: A Reddit username that the RedditBot will use.
        """
        super(RedditBot, self).__init__()
        self.USER_NAME = user_name or 'FAUbot'
        self.USER_AGENT = user_agent or RedditBot.debug_user_agent_template.format(username=self.USER_NAME)
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

    def get_commands(self):  # todo function for getting commands from PMs/messages
        return []

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
        r = praw.Reddit(user_agent=self.USER_AGENT, site_name=self.USER_NAME)
        try:
            current_access_info = r.refresh_access_information()
        except praw.errors.HTTPException:
            raise MissingRefreshTokenError("No oauth refresh token saved. Please run account_register.py.")
        r.set_access_credentials(**current_access_info)
        return r


class ExampleBot(RedditBot):
    """
    An example RedditBot to show how simple it is to create new bots.
    Only a constructor and a work function are needed.
    """
    def __init__(self, user_agent=None, user_name=None):
        super(ExampleBot, self).__init__(user_agent, user_name)

    def work(self):
        me = self.r.get_me()
        print("ExampleBot working...Username: {}  Link karma: {}".format(me.name, me.link_karma))
        sleep(2)


class Dispatch(threading.Thread, metaclass=ABCMeta):
    """
    An object used to create, launch, and terminate bots.
    """
    def __init__(self, bot_signatures, stop_event=None):
        """
        Initializes a Dispatch object, and creates a pool of bots.
        :param bot_signatures: A list of BotSignatures used to create the new bots
        :param stop_event: A threading.Event used to keep the Dispatch alive and tell it when to close.
        """
        super(Dispatch, self).__init__()
        self.stop = stop_event or threading.Event()
        self.bots = {sig.username: BOT_CLASSES[sig.classname](user_agent=None, user_name=sig.username)
                     for sig in bot_signatures}

    def __enter__(self):
        """
        Starts a Dispatch using a context manager,
        e.g. with Dispatch():
                 # do something
        :return: The dispatch object
        """
        self.start()
        return self

    def __exit__(self):
        """
        Safely closes a Dispatch using a context manager,
        e.g. with Dispatch():
                 # do something
        """
        self.join()

    def run(self):
        """
        Override of Thread.run().
        Starts the bots, and waits for a stop event.
        :return:
        """
        for name, bot in self.bots.items():
            bot.start()
        self.stop.wait()

    def join(self, timeout=None):
        """
        Override of Thread.join().
        Stops all the bots, sets the stop event, and stops itself.
        :param timeout: Time to wait before forcefully stopping itself (wait forever if None).
        :return: Original return value of Thread.join()
        """
        for bot in self.bots.values():
            bot.join(timeout)
        self.stop.set()
        return super(Dispatch, self).join(timeout)


class GlobalDispatch(Dispatch):
    """
    A Dispatch that creates Bots with every entry in praw.ini.
    It assumes every entry is meant to be used for a Bot.
    """
    def __init__(self, stop_event=None):
        """
        Creates BotSignatures for every account in praw.ini, and initializes a Dispatch.
        :param stop_event: A threading.Event used to stop the Dispatch.
        """
        signatures = [BotSignature(classname=praw_config.get_bot_class_name(name),
                                   username=name,
                                   useragent=RedditBot.debug_user_agent_template.format(username=name),  # todo no debug
                                   permissions=praw_config.get_reddit_oauth_scope(name))
                      for name in praw_config.get_all_site_names()]
        super(GlobalDispatch, self).__init__(signatures, stop_event)


BOT_CLASSES = {
    Bot.__name__: Bot,
    RedditBot.__name__: RedditBot,
    ExampleBot.__name__: ExampleBot
}

if __name__ == '__main__':
    with GlobalDispatch():
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            # This doesn't work in the PyCharm run window, but it works in Powershell.
            pass
