import requests
import datetime
from cachetools import ttl_cache
from collections import namedtuple
from bs4 import BeautifulSoup
from random import randint
from config import getLogger
from config.bot_config import get_interval
from bots import RedditBot

# region constants
SUBMISSION_INTERVAL_HOURS = get_interval('submission_interval_hours')
# endregion

# region globals
logger = getLogger()
Link = namedtuple('Link', 'url title')
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
    def __init__(self, user_name, *args, **kwargs):
        super(NewsBot, self).__init__(user_name=user_name, *args, **kwargs)
        self.base_url = "http://www.upressonline.com"
        self._last_created = None


    @ttl_cache(ttl=86400)
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
        return self._get_link_list(url)

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
        return self._get_link_list(url)
    
    @ttl_cache(ttl=600)  # cache for 10 minutes todo configurable ttl
    def _get_link_list(self, url):
        """
        Parses a web page's HTML for links with a particular attribute (rel=bookmark),
        which are assumed to be links to articles on the school paper's website.
        :param url: The url to the page that should contain links to articles
        :raises ValueError if the HTTP response is anything but 200 OK.
        :return: A list of Links (namedtuples)
        """
        link_list = []
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            soup = BeautifulSoup(r.content, 'html.parser')
            for link in soup.find_all(rel='bookmark'):
                url = link['href']
                title = link.get_text().replace("“", '"').replace("”", '"').replace("’", "'")
                link_list.append(Link(url=url, title=title))
            return link_list
        elif r.status_code == requests.codes.not_found:
            logger.info("No links found: url=[{}], code=[{}]".format(url, r.status_code))
            return link_list
        else:
            raise ValueError("Error talking to UPress: url=[{}], code=[{}]".format(url, r.status_code))

    def submit_link(self, link_tuple):
        """
        Submit a link to Reddit, and save the submission time to the database.
        :param link_tuple: A namedtuple with a url and a title.
        """
        for subreddit in self.subreddits:
            if self.is_already_submitted(link_tuple.url, subreddit):
                logger.info("Link already submitted: subreddit=[{}], url=[{}]".format(subreddit, link_tuple.url))
                # sleep for shorter time if time to submit but random article was already submitted
                self.sleep_interval = 5
            else:
                logger.info("Submitting link: subreddit=[{}], url=[{}]".format(subreddit, link_tuple.url))
                self.r.submit(subreddit, link_tuple.title, url=link_tuple.url)
                self._last_created = datetime.datetime.utcnow()

    @staticmethod
    def _get_random_article(articles):
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
        msg = "Random article: url=[{}], title=[{}]".format(article.url, article.title) if article \
            else "Empty list provided. Returning None."
        logger.info(msg)
        return article

    def get_random_article_from_today(self):
        """
        High level function to get articles published today and return a random one.
        :return: A Link representing a random article that was published on the current day.
        """
        articles = self.get_articles_from_today()
        return NewsBot._get_random_article(articles)

    def get_random_article_by_date(self, year, month=None, day=None):
        """
        Get articles from a certain date, and return a random one.
        :param year:
        :param month:
        :param day:
        :return: A Link representing a random article that was published on a certain date.
        """
        articles = self.get_articles_by_date(year, month, day)
        return NewsBot._get_random_article(articles)

    def get_random_article_by_category(self, category, subcategory=None):
        """
        Get articles from a certain category, and return a random one.
        :param category:
        :param subcategory:
        :return: A Link representing a random article that was published in a certain category.
        """
        articles = self.get_articles_by_category(category, subcategory)
        return NewsBot._get_random_article(articles)

    def do_scheduled_submit(self):
        """
        Check if enough time has passed since the last submission. If it has, submit a new link and save the current
        submission time. This is the NewsBot's main logic function.
        """
        if self.is_time_to_submit():
            # You can hard code article date while developing. Production bot will get article from current day.
            # article = self.get_random_article_by_date(2014, 10)
            article = self.get_random_article_from_today()
            if article:
                self.submit_link(article)
            else:
                logger.info("No articles have been published yet today.")
        else:
            logger.info("Not time to submit.")

    @staticmethod
    def _check_difference(now, last, target_interval):
        difference = now - last
        if difference < target_interval:
            logger.info("Not time to submit: currentTime=[{}], lastSubmissionTime=[{}], "
                                "difference=[{:5.2f} hrs]".format(now, last, (difference.seconds/60)/60))
            return False
        return True

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

        if self._last_created:
            is_time = self._check_difference(now, self._last_created, target_interval)
        else:
            for post in me.get_submitted(sort="new", time="day"):
                if post.url.startswith(self.base_url):
                    created = datetime.datetime.utcfromtimestamp(post.created_utc)
                    if not self._check_difference(now, created, target_interval):
                        is_time = False
                        break
        if is_time:
            logger.info("Time to submit article. currentTime=[{}]".format(now))
        return is_time

    def work(self):
        self.do_scheduled_submit()


def main():
    from config.praw_config import get_all_site_names
    from argparse import ArgumentParser
    parser = ArgumentParser("Running EventBot by itself")
    parser.add_argument("-a", "--account", dest="reddit_account", required=True, choices=get_all_site_names(),
                        help="Specify which Reddit account entry from praw.ini to use.")
    args = parser.parse_args()
    test = NewsBot(args.reddit_account, run_once=True)
    test.start()
    test.stop_event.wait()


if __name__ == '__main__':
    main()
