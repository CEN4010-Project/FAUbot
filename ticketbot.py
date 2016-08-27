import re
from config import getLogger
from bots import RedditBot

logger = getLogger()


class TicketBot(RedditBot):
    def __init__(self, user_name, *args, **kwargs):
        super().__init__(user_name, *args, **kwargs)
        self.COMMAND_PATTERN = "!FAUbot (buy|sell) (\d{1,2})"

    def work(self):
        logger.info("Getting unread messages")
        inbox = self.r.get_unread(unset_has_mail=True)
        for message in inbox:
            command = re.search(self.COMMAND_PATTERN, message.body)
            if command:
                logger.info("Found message with a command")
                operation = command.groups()[0]
                number = command.groups()[1]
                logger.info("Command: operation=[{}], number=[{}]".format(operation, number))
                subject = "FAUbot received your command"
                reply = """Hello! You have sent me a command. According to the message you sent me, you want to:

`{} {}` ticket{}.

Right now I'm just a prototype, so I will not process your request.""".format(operation, number, ('s' if int(number) > 1 else ''))
                logger.info("Sending reply to: recipient=[{}]".format(message.author))
                self.r.send_message(message.author, subject, reply)
                logger.info("Message sent.")
                message.mark_as_read()


def main():
    from config.praw_config import get_all_site_names
    from argparse import ArgumentParser
    parser = ArgumentParser("Running TicketBot by itself")
    parser.add_argument("-a", "--account", dest="reddit_account", required=True, choices=get_all_site_names(),
                        help="Specify which Reddit account entry from praw.ini to use.")
    args = parser.parse_args()
    test = TicketBot(args.reddit_account, run_once=True)
    test.start()
    test.stop_event.wait()


if __name__ == '__main__':
    main()



if __name__ == '__main__':
    bot = TicketBot('FAUbot', run_once=True)
    bot.start()
    bot.stop_event.wait()
