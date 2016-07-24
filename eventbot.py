from bs4 import BeautifulSoup
from dateutil import parser
import requests
import datetime
import json

# Scrape the information from the upressonline
r = requests.get("http://www.upressonline.com/fauevents/")
data = r.text
soup = BeautifulSoup(data, "html.parser")
#print(soup.prettify())

now = datetime.datetime.utcnow()
#dt_now = parser.parse(now)
print(now)
#timestamp = "January 1, 2016"
#dt_object = parser.parse(timestamp)
#print(dt_object)



data = []
titles = []  # 3
dates = []  # 6
descriptions = []  # 8
times = []
fmt = '{:<8}{:<55}{:<75}{}'
print(fmt.format('', 'Title', 'Date', 'Description'))
i = 1

for event in soup.find_all('div', attrs={'data-tribejson': True}):
    event_json = event.get('data-tribejson')
    event_dict = json.loads(event_json)
    titles.append(event_dict['title'])
    dates.append(event_dict['dateDisplay'])
    times.append(event_dict['startTime'])
    descriptions.append(event_dict['excerpt'][3:-4])
    # the excerpt is still in a <p> tag, so I use string indexing to get only the text inside the tags.

#print(titles)


#for time in times:
    oldstr = event_dict['startTime']
    timestamp = oldstr.replace("@", "")
    #print(timestamp)
    dt = parser.parse(timestamp)
    # #print(dt)
    if dt >= now:
        print(fmt.format(i, event_dict['title'], event_dict['dateDisplay'], event_dict['excerpt'][3:-4]))
        i += 1





# fmt = '{:<8}{:<25}{:<75}{}'
#
# print(fmt.format('', 'Title', 'Date', 'Description'))
# for i, (title, date, descrip) in enumerate(zip(titles, dates, descriptions)):
#     print(fmt.format(i, title, date, descrip))
