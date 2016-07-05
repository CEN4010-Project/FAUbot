import requests
import datetime
from collections import namedtuple
from bs4 import BeautifulSoup
from random import randint
from time import sleep
import boto3
import boto3.dynamodb
from config import getLogger
from config.bot_config import CONFIG
from bots import RedditBot


# region constants
UTC_TIMESTAMP_FORMAT = CONFIG['formats']['utc_timestamp']
SUBMISSION_INTERVAL_HOURS = CONFIG['intervals']['submission_interval_hours']
# endregion

# region globals
logger = getLogger()
Link = namedtuple('Link', 'url title')
"""
A namedtuple is just a regular tuple, e.g. (2, 'a', 5), which is an iterable container that is immutable,
meaning you cannot change a value in it or add/remove values to/from it.

The difference between a regular tuple and a namedtuple is that each value in a namedtuple has its own name. It's
just an easy way to refer to the values in the tuple.

The 'Link' namedtuple looks like this Link(url="www.example.com/article/1", title="This is the title")
It has two values. The first is the link's URL, and the second is the title of the web page.

So instead of having to use Link[0] for the URL and Link[1] for the title, I can say Link.url and Link.title
"""
# endregion


# region helpers
def clean_dir(obj):
    """
    When you want to call dir() on something but don't want to see any private attributes/methods.
    This is just a helper function used to figure out what attributes/methods an object has.
    :param obj: The thing to call dir() on, e.g. dir(obj)
    :return: A list of public methods and/or attributes of the object.
    """
    return [d for d in dir(obj) if not d.startswith('_') and not d.endswith('_')]
# endregion


class NewsBot(RedditBot):
    def __init__(self, *args, **kwargs):
        super(NewsBot, self).__init__(user_agent="/r/FAUbot posting FAU news to Reddit", user_name="FAUbot")
        self.base_url = "http://www.upressonline.com"
        self.subreddits = CONFIG.get('subreddits', None) or ['FAUbot']
        self._populate_table_if_needed()

    @staticmethod
    def _get_submission_table():
        db = boto3.resource('dynamodb', region_name='us-east-1')
        return db.Table('bot_submission_history')

    def _populate_table_if_needed(self):
        table = self._get_submission_table()
        if not self.get_submission_record(table):
            logger.info("No submission record found. Creating a new one.")
            table.put_item(
                Item={'bot_name': NewsBot.__name__}
            )

    def is_already_submitted(self, url, subreddit):
        """
        Checks if a URL has already been shared on self.subreddit.
        Because praw.Reddit.search returns a generator instead of a list,
        we have to actually loop through it to see if the post exists.
        If no post exists, the loop won't happen and it will return False.
        :param url: The url that will be searched for
        :param subreddit: The subreddit where the url will be searched for
        :return: True if the url has already been posted to the subreddit
        """
        for link in self.r.search("url:"+url, subreddit=subreddit):
            if link:
                return True
        return False

    def get_articles_from_today(self):
        """
        Gets all articles posted to upressonline.com on today's date.
        :return: a list of Links (namedtuples) with url and title elements.
        """
        today = datetime.datetime.today()
        return self.get_articles_by_date(today.year, today.month, today.day)

    def get_articles_by_category(self, category_name, category_subname=None):
        """
        Get all articles tagged with a certain category name, e.g. category/reviews, or category/news.
        A category subname may be provided, e.g. category/reviews/books, or category/sports/baseball.
        :param category_name: Name of the category
        :param category_subname: Subname of the category
        :return: list of Links (namedtuples)
        """
        url = "{}/category/{}".format(self.base_url, category_name)
        if category_subname:
            url = "{}/{}".format(url, category_subname)
        return NewsBot._get_link_list(url)

    def get_articles_by_date(self, year, month=None, day=None):
        """
        Gets articles posted on a certain date.
        The only required parameter is year. Day cannot be provided without month.
        Any dates before 1995 are invalid since that's the year of the oldest post on the website.
        :param year:
        :param month:
        :param day:
        :raises ValueError if the year is too early or too late
        :raises ValueError if a day is specified without the month
        :return: list of Links (namedtuples)
        """
        if not year or not 1995 <= year <= datetime.datetime.today().year:
            raise ValueError("Invalid year parameter.")
        url = "{}/{}".format(self.base_url, year)
        if month:
            url = "{}/{:02}".format(url, month)
            if day:
                url = "{}/{:02}".format(url, day)
        elif day:
            raise ValueError("Cannot specify day without month.")
        return NewsBot._get_link_list(url)

    @staticmethod
    def _get_link_list(url):
        """
        Parses a web page's HTML for links with a particular attribute (rel=bookmark),
        which are assumed to be links to articles on the school paper's website.
        :param url: The url to the page that should contain links to articles
        :raises ValueError if the HTTP response is anything but 200 OK.
        :return: A list of Links (namedtuples)
        """
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            soup = BeautifulSoup(r.content, 'html.parser')
            link_list = []
            for link in soup.find_all(rel='bookmark'):
                url = link['href']
                title = link.get_text().replace("“", '"').replace("”", '"')
                link_list.append(Link(url=url, title=title))
            return link_list
        else:
            raise ValueError("Invalid Url: {}    HTTP status code: {}".format(url, r.status_code))

    def submit_link(self, link_tuple):
        """
        Submit a link to Reddit, and save the submission time to the database.
        :param link_tuple: A namedtuple with a url and a title.
        """
        for subreddit in self.subreddits:
            if not self.is_already_submitted(link_tuple.url, subreddit):
                logger.info("Submitting link. subreddit=[{}], url=[{}]".format(subreddit, link_tuple.url))
                self.r.submit(subreddit, link_tuple.title, url=link_tuple.url)
            else:
                logger.info("Link already submitted. subreddit=[{}], url=[{}]".format(subreddit, link_tuple.url))

    @staticmethod
    def _get_random_articles(articles):
        """
        A private helper function that takes a list of Links and returns a random one.
        If the list is empty, this function returns None.
        :type articles: list
        :param articles: list of Links
        :return: a random Link
        """
        if len(articles) > 1:
            random_index = randint(0, len(articles))
            article = articles[random_index-1]
        elif articles:
            article = articles[0]
        else:
            article = None
        return article

    def get_random_article_from_today(self):
        articles = self.get_articles_from_today()
        return NewsBot._get_random_articles(articles)

    def get_random_article_by_date(self, year, month=None, day=None):
        articles = self.get_articles_by_date(year, month, day)
        return NewsBot._get_random_articles(articles)

    def get_random_article_by_category(self, category, subcategory=None):
        articles = self.get_articles_by_category(category, subcategory)
        return NewsBot._get_random_articles(articles)

    def set_last_submission_time(self, table=None):
        table = table or self._get_submission_table()
        now = datetime.datetime.utcnow()
        time_stamp = now.strftime(UTC_TIMESTAMP_FORMAT)
        table.update_item(
            Key={'bot_name': self.__class__.__name__},
            UpdateExpression='SET last_submission_time = :val1',
            ExpressionAttributeValues={':val1': time_stamp}
        )

    def get_last_submission_time(self, table=None):
        submission_record = self.get_submission_record(table)
        try:
            return submission_record['last_submission_time']
        except (TypeError, KeyError):
            return None

    def get_submission_record(self, table=None):
        table = table or self._get_submission_table()
        response = table.get_item(
            Key={'bot_name': self.__class__.__name__}
        )
        try:
            return response['Item']
        except KeyError:
            return None

    def is_time_to_submit(self, submission_table=None):
        last_submission_time = datetime.datetime.strptime(self.get_last_submission_time(submission_table), UTC_TIMESTAMP_FORMAT)
        target_interval = datetime.timedelta(hours=SUBMISSION_INTERVAL_HOURS)
        return datetime.datetime.utcnow() - last_submission_time >= target_interval

    def do_scheduled_submit(self):
        table = self._get_submission_table()
        if self.is_time_to_submit(table):
            logger.info("Time to submit.")
            article = self.get_random_article_by_date(2016, 2)  # for now, get from a month with plenty of articles
            self.submit_link(article)
            self.set_last_submission_time(table)
        else:
            logger.info("Not time to submit. Sleeping...")

    def work(self):
        self.do_scheduled_submit()
