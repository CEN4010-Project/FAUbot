from collections import namedtuple
from config import getLogger
from bs4 import BeautifulSoup
import requests
import datetime
import string
import json
from pytz import timezone, utc
from dateutil.parser import parse
from bots import RedditBot
from config.bot_config import CONFIG


# region constants
SUBMISSION_INTERVAL_HOURS = CONFIG['intervals']['submission_interval_hours']
SUBREDDITS = CONFIG['subreddits']
# endregion


BASE_URL = "http://www.upressonline.com/fauevents/"
TABLE_ROW = "{title} | {date} | {description}\n"
HYPERLINK = "[{text}]({url})"
HEADER_DIVIDER = "---|---|----\n"
TABLE_HEADER = TABLE_ROW.format(title='Title', date='Date', description='Description') + HEADER_DIVIDER
logger = getLogger()


"""
To use string formatting on the HYPERLINK template, you have to use keyword arguments, e.g.

link = HYPERLINK.format(text="Click Me", url="http://example.com")

This will let you put links inside your Reddit posts.
"""


class EventBot(RedditBot):
    def __init__(self, user_name, *args, **kwargs):
        super(EventBot, self).__init__(user_name=user_name, *args, **kwargs)
        self.base_url = BASE_URL
        self.subreddits = CONFIG.get('subreddits', None) or ['FAUbot']
        self.post_title = "Event Calendar"

    @staticmethod
    def has_event_passed(event_json):
        event_dict = EventBot._get_event_dict(event_json)
        timestamp = event_dict['date']
        invalidChars = set(string.punctuation)
        if any(char in invalidChars for char in timestamp):
            full_date = timestamp.replace(" @ ", " ")
            dash_idx = full_date.index('-')
            date = full_date[:dash_idx - 1]
            start_datetime = timezone("US/Eastern").localize(parse(date), is_dst=None).astimezone(utc)
        else:
            date = timestamp
            start_datetime = timezone("US/Eastern").localize(parse(date), is_dst=None).astimezone(utc)

        now = utc.localize(datetime.datetime.utcnow())  # get current time in UTC timezone
        return now > start_datetime  # True if now is after start time

    def get_title(event_json):
        event_dict = EventBot._get_event_dict(event_json)
        title = event_dict['title']
        return title


    @staticmethod
    def _get_event_html():
        """
        Makes the HTTP request to the event calendar website.
        :return: String containing HTML, or None if the response is not 200 OK.
        """
        logger.info("Getting event calendar HTML from {}".format(BASE_URL))
        r = requests.get(BASE_URL)
        if r.status_code == requests.codes.ok:
            data = r.text
            return data
        logger.warning("Returning None, Response not OK: code={}".format(r.status_code))
        return None

    @staticmethod
    def _get_event_dict(event_json):
        """
        Takes the relevant values out of the event JSON and creates a simpler dictionary
        that is used to format the string TABLE_ROW.
        :param event_json: JSON stripped from the event's data-tribejson HTML attribute.
        :type event_json: str
        :return: A dict containing the relevant event data
        """
        event_dict = json.loads(event_json)
        return {'title': HYPERLINK.format(text=event_dict['title'], url=event_dict['permalink']),
                'date': event_dict['dateDisplay'],
                'description': event_dict['excerpt'][3:-4] or "None provided",}

    @staticmethod
    def _make_reddit_table(html):
        """
        Scrapes event data from HTML and creates a Reddit table with it.
        :param html: HTML from the event website
        :type data: str
        :return: A single string containing a Reddit markdown table
        """
        logger.info("Generating reddit table")

        # start with the header, and append a new row for each event
        table = TABLE_HEADER
        soup = BeautifulSoup(html, "html.parser")
        for event in soup.find_all('div', attrs={'data-tribejson': True}):
            event_json = event.get('data-tribejson')
            event_dict = EventBot._get_event_dict(event_json)
            if EventBot.has_event_passed(event_json) is False:
                table += TABLE_ROW.format(**event_dict)
        return table

    def get_reddit_table(self):
        """
        Uses all the helper functions to get the HTML, scrape it, and generate a Reddit table.
        :return: A single string containing a Reddit markdown table, or None if an error happens.
        """
        table = None
        html = self._get_event_html()
        if html:
            table = EventBot._make_reddit_table(html)
        else:
            logger.error("Table could not be generated.")
        return table


    def get_existing_table_post(self,title, subreddit):
        """
         Checks if a URL has already been shared on self.subreddit.
         Because praw.Reddit.search returns a generator instead of a list,
         we have to actually loop through it to see if the post exists.
         If no post exists, the loop won't happen and it will return False.
         :param post: The url that will be searched for
         :param subreddit: The subreddit where the url will be searched for
         :return: True if the url has already been posted to the subreddit
         """
        for post in self.r.search("title:{} AND author:{}".format(title, self.USER_NAME), subreddit=subreddit):
            if post:
                return post
        return None

    def create_new_table(self):
        html = self._get_event_html()
        table = self._make_reddit_table(html)
        return table

    def submit_new_table(self, table):
        """
        Submit a link to Reddit, and save the submission time to the database.
        :param title_tuple: A namedtuple with a url and a title.
        """
        title = self.post_title
        for subreddit in self.subreddits:
            self.r.submit(subreddit, title, text = table)
            print(table)


    def work(self):
        html = self._get_event_html()
        soup = BeautifulSoup(html, "html.parser")
        for event in soup.find_all('div', attrs={'data-tribejson': True}):
            event_json = event.get('data-tribejson')
        title = self.get_title(event_json)
        table = self.create_new_table()
        for subreddit in self.subreddits:
            existing_post = self.get_existing_table_post(title, subreddit)
            if existing_post:  # if it exists
                logger.info("Table already submitted")
                existing_post.edit(table)
            else:
                logger.info("Submitting Table")
                self.submit_new_table(table)  # I added the word 'new' to be more specific


def main():
    test = EventBot('FAUbot', run_once=True)  # the bot will only do one loop if you set that to True
    test.start()
    test.stop_event.wait() #this keeps the program alive while the bot does its work in a separate


if __name__ == '__main__':
    main()

