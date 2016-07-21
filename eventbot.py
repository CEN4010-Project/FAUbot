from config import getLogger
from bs4 import BeautifulSoup
import requests
import json

from bots import RedditBot

BASE_URL = "http://www.upressonline.com/fauevents/"
TABLE_ROW = "{title} | {date} | {description}\n"
HEADER_DIVIDER = "---|---|----\n"
TABLE_HEADER = TABLE_ROW.format(title='Title', date='Date', description='Description') + HEADER_DIVIDER
logger = getLogger()


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


def _get_event_dict(event_json):
    """
    Takes the relevant values out of the event JSON and creates a simpler dictionary
    that is used to format the string TABLE_ROW.
    :param event_json: JSON stripped from the event's data-tribejson HTML attribute.
    :type event_json: str
    :return: A dict containing the relevant event data
    """
    event_dict = json.loads(event_json)
    return {'title': event_dict['title'],
            'date': event_dict['dateDisplay'],
            'description': event_dict['excerpt'][3:-4] or "None provided"}


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
        event_dict = _get_event_dict(event_json)
        table += TABLE_ROW.format(**event_dict)
    return table


def get_reddit_table():
    """
    Uses all the helper functions to get the HTML, scrape it, and generate a Reddit table.
    :return: A single string containing a Reddit markdown table, or None if an error happens.
    """
    table = None
    html = _get_event_html()
    if html:
        table = _make_reddit_table(html)
    else:
        logger.error("Table could not be generated.")
    return table


class EventBot(RedditBot):
    def __init__(self, user_name, *args, **kwargs):
        super().__init__(user_name, *args, **kwargs)
        self.base_url = BASE_URL

    def work(self):
        table = get_reddit_table()
        print(table)


def main():
    table = get_reddit_table()
    print(table)

if __name__ == '__main__':
    main()
