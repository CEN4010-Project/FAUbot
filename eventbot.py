from collections import namedtuple

from config import getLogger
from bs4 import BeautifulSoup
import requests
import datetime
import json
from pytz import timezone, utc
from dateutil.parser import parse
from bots import RedditBot
from config.bot_config import CONFIG


# region constants
SUBMISSION_INTERVAL_HOURS = CONFIG['intervals']['submission_interval_hours']
SUBREDDITS = CONFIG['subreddits']
# endregion

title = namedtuple('title', 'date')

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

    @staticmethod
    def has_event_passed(event_json):
        event_dict = EventBot._get_event_dict(event_json)
        timestamp = event_dict['date']
        full_date = timestamp.replace(" @ ", " ")
        dash_idx = full_date.index('-')
        date = full_date[:dash_idx - 1]
        start_datetime = timezone("US/Eastern").localize(parse(date), is_dst=None).astimezone(utc)
        now = utc.localize(datetime.datetime.utcnow())  # get current time in UTC timezone
        return now > start_datetime  # True if now is after start time

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

    def is_already_submitted(self, title, subreddit):
        """
        Checks if a URL has already been shared on self.subreddit.
        Because praw.Reddit.search returns a generator instead of a list,
        we have to actually loop through it to see if the post exists.
        If no post exists, the loop won't happen and it will return False.
        :param url: The url that will be searched for
        :param subreddit: The subreddit where the url will be searched for
        :return: True if the url has already been posted to the subreddit
        """
        for title in self.r.search("title:"+title, subreddit=subreddit):
            if title:
                return True
        return False

    def edit_existing_table(self):
        html = self._get_event_html()
        table = self._make_reddit_table(html)
        return table

    def create_new_table(self):
        html = self._get_event_html()
        table = self._make_reddit_table(html)
        return table

    def submit_table(self, title_tuple):
        """
        Submit a link to Reddit, and save the submission time to the database.
        :param link_tuple: A namedtuple with a url and a title.
        """
        for subreddit in self.subreddits:
            if self.is_already_submitted(title_tuple.title, subreddit):
                logger.info("Table already submitted: subreddit=[{}], title=[{}]".format(subreddit, title_tuple.title))
                table = self.edit_exisiting_table()
                # sleep for shorter time if time to submit but random article was already submitted
                self.sleep_interval = 5
                print(table)

            else:
                logger.info("Submitting link: subreddit=[{}], url=[{}]".format(subreddit, title_tuple.title))
                self.r.submit(subreddit, title_tuple.title, url=title_tuple.url)
                table = self.create_new_table()
                print(table)


    def do_scheduled_submit(self,event_json):
        """
        Check if enough time has passed since the last submission. If it has, submit a new link and save the current
        submission time. This is the NewsBot's main logic function.
        """
        if self.is_time_to_submit():
            event_dict = EventBot._get_event_dict(event_json)
            title = event_dict['title']
            if title:
                self.submit_table(title)
            else:
                logger.info("No articles have been published yet today.")
        else:
            logger.info("Not time to submit.")

    def is_time_to_submit(self):
        """
        Check if enough time has passed to submit another article.
        This function checks the creation time of FAUbot's newest submissions. If at least 24 hours has passed since the
        last article submission, it is time to submit a new article. The 24 hour interval is configurable in
        config/bot_config.yaml.
        :return: True if enough time has passed for a new article to be submitted.
        """
        is_time = True
        me = self.r.get_me()
        now = datetime.datetime.utcnow()
        target_interval = datetime.timedelta(hours=SUBMISSION_INTERVAL_HOURS)
        logger.info("Checking if time to submit: targetInterval=[{}]".format(target_interval))
        for post in me.get_submitted(sort="new", time="day"):
            if post.url.startswith(self.base_url):
                created = datetime.datetime.utcfromtimestamp(post.created_utc)
                difference = now - created
                if difference < target_interval:
                    logger.info("Not time to submit: currentTime=[{}], lastSubmissionTime=[{}], "
                                "difference=[{:5.2f} hrs]".format(now, created, (difference.seconds/60)/60))
                    is_time = False
                    break
        else:
            logger.info("Time to submit article. currentTime=[{}]".format(now))
        return is_time



    def work(self):
        table = self.get_reddit_table()
        self.submit_table(title)


def main():
    test = EventBot(RedditBot, run_once=True)  # the bot will only do one loop if you set that to True
    test.work()


if __name__ == '__main__':
    main()

