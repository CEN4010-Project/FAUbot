import re
from config import getLogger
from bots import RedditBot

logger = getLogger()


class TicketBot(RedditBot):
    def __init__(self, user_name, *args, **kwargs):
        super().__init__(user_name, *args, reset_sleep_interval=False, **kwargs)
        self.COMMAND_PATTERN = "!FAUbot (buy|sell) (\d{1,2})"
        self.sleep_interval = 5

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


if __name__ == '__main__':
    bot = TicketBot('FAUbot', run_once=True)
    bot.start()
    bot.stop_event.wait()
