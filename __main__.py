import threading
from abc import ABCMeta
from time import sleep
from argparse import ArgumentParser

import newsbot  # you must import your bot file here, even if you don't use it
import eventbot
import ticketbot
import config
from config import praw_config, bot_config
from bots import InvalidBotClassName, BotSignature, RedditBot


# If you declare your own RedditBot subclass in its own file,
# you must import it or else it will not be added to BOT_CLASSES.
BOT_CLASSES = {cls.__name__: cls for cls in RedditBot.get_subclasses()}

logger = config.getLogger()
parser = ArgumentParser(description="FAUbot options")
parser.add_argument("-a", "--account", dest='account', choices=praw_config.get_all_site_names(),
                    help="Specify which Reddit account configured in praw.ini will be used to launch bots.")


# region DISPATCH
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
        self.bots = {}

        for signature in bot_signatures:
            if type(signature.classname) is str:
                self.bots[signature.classname] = [BOT_CLASSES[name](user_name=signature.username)
                                                  for name in signature.classname.split(",")]
            elif type(signature.classname) is list and all(type(name) is str for name in signature.classname):
                self.bots[signature.classname] = [BOT_CLASSES[name](user_name=signature.username)
                                                  for name in signature.classname]
            else:
                raise InvalidBotClassName
        pass

    def __enter__(self):
        """
        Starts a Dispatch using a context manager,
        e.g. with Dispatch():
                 # do something
        :return: The dispatch object
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
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
        for bot_list in self.bots.values():
            for bot in bot_list:
                bot.start()
        self.stop.wait()

    def join(self, timeout=None):
        """
        Override of Thread.join().
        Stops all the bots, sets the stop event, and stops itself.
        :param timeout: Time to wait before forcefully stopping itself (wait forever if None).
        :return: Original return value of Thread.join()
        """
        for bot_list in self.bots.values():
            for bot in bot_list:
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
        signatures = [_generate_bot_signature(name) for name in praw_config.get_all_site_names()]
        super(GlobalDispatch, self).__init__(signatures, stop_event)
# endregion


def _generate_bot_signature(name):
    return BotSignature(classname=praw_config.get_bot_class_name(name), username=name,
                        permissions=praw_config.get_reddit_oauth_scope(name))


def _get_dispatch(cli_args):
    if cli_args.account:
        return Dispatch, [_generate_bot_signature(cli_args.account)]
    else:
        return GlobalDispatch, None


def main(args=None):
    cli_args = parser.parse_args()
    dispatch, params = _get_dispatch(cli_args)

    logger.info("Starting bots")
    with dispatch(params):
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            logger.info("Terminating bots")
    logger.info("Program closed")


if __name__ == '__main__':
    main()
