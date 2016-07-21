from bs4 import BeautifulSoup
import requests
import json

# Scrape the information from the upressonline
r = requests.get("http://www.upressonline.com/fauevents/")
data = r.text
soup = BeautifulSoup(data, "html.parser")
print(soup.prettify())

data = []
titles = []  # 3
dates = []  # 6
descriptions = []  # 8

for event in soup.find_all('div', attrs={'data-tribejson': True}):
    event_json = event.get('data-tribejson')
    event_dict = json.loads(event_json)
    titles.append(event_dict['title'])
    dates.append(event_dict['dateDisplay'])
    descriptions.append(event_dict['excerpt'][3:-4])
    # the excerpt is still in a <p> tag, so I use string indexing to get only the text inside the tags.

fmt = '{:<8}{:<25}{:<75}{}'

print(fmt.format('', 'Title', 'Date', 'Description'))
for i, (title, date, descrip) in enumerate(zip(titles, dates, descriptions)):
    print(fmt.format(i, title, date, descrip))
