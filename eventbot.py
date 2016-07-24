from config import getLogger
from bs4 import BeautifulSoup
from dateutil import parser
import requests
import datetime
import json
from pytz import timezone, utc
from dateutil.parser import parse
from bots import RedditBot


BASE_URL = "http://www.upressonline.com/fauevents/"
TABLE_ROW = "{title} | {date} | {description}\n"
HEADER_DIVIDER = "---|---|----\n"
TABLE_HEADER = TABLE_ROW.format(title='Title', date='Date', description='Description') + HEADER_DIVIDER
logger = getLogger()


class EventBot(RedditBot):
    def __init__(self, user_name, *args, **kwargs):
        super(EventBot, self).__init__(user_name = user_name, *args, **kwargs)
        self.base_url = BASE_URL

    def has_event_passed(timestamp):
        full_date = timestamp.replace(" @ ", " ")
        dash_idx = full_date.index('-')
        date = full_date[:dash_idx - 1]
        start_datetime = timezone("US/Eastern").localize(parse(date), is_dst=None).astimezone(utc)
        now = utc.localize(datetime.datetime.utcnow())  # get current time in UTC timezone
        return now > start_datetime  # True if now is after start time


    def _get_event_html(self):
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
                'description': event_dict['permalink'] or "None provided"}

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
            event_dict = html._get_event_dict(event_json)
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
            table = self._make_reddit_table(html)
        else:
            logger.error("Table could not be generated.")
        return table

    def work(self):
        table = self.get_reddit_table()
        print(table)

def main():
    test = EventBot(RedditBot)
    table = test.get_reddit_table()
    print(table)

if __name__ == '__main__':
    main()


# for event in soup.find_all('div', attrs={'data-tribejson': True}):
#     event_json = event.get('data-tribejson')
#     event_dict = json.loads(event_json)
#     titles.append(event_dict['title'])
#     dates.append(event_dict['dateDisplay'])
#     times.append(event_dict['permalink'])
#     descriptions.append(event_dict['excerpt'][3:-4])
#     # the excerpt is still in a <p> tag, so I use string indexing to get only the text inside the tags.
#
# #print(titles)
#
#
# #for time in times:
#     timestamp = event_dict['dateDisplay']
#     #timestamp = oldstr.replace("@", "")
#     #print(timestamp)
#     #dt = parser.parse(timestamp)
#     # #print(dt)
#     if has_event_passed(timestamp) is False:
#         print(fmt.format(i, event_dict['title'], event_dict['dateDisplay'], event_dict['permalink']))
#         i += 1




