from bs4 import BeautifulSoup
import requests

#Scrape the information from the upressonline
r  = requests.get("http://www.upressonline.com/fauevents/")
data = r.text
soup = BeautifulSoup(data, "lxml")
print(soup.prettify())

data = []
titles = []  #3
dates = [] #6
descrips = [] #8


for events in soup.find_all('div'):
        if (events.get('data-tribejson') is not None):
            #i = 0
            event = events.get('data-tribejson')
            data = event.split(",")

            title = data[3]
            a,t= title.split(":",1)
            if t.startswith('"') and t.endswith('"'):
                t = t[1:-1]
                titles.append(t)

            date = data[6]
            b,d= date.split(":",1)
            if d.startswith('"') and d.endswith('"'):
                d = d[1:-1]
                dates.append(d)

            descrip = data[8]
            c,f= descrip.split(":",1)
            #print(f)
            #if f.startswith('"') and f.endswith('"'):
                #f = f[1:-1]
            descrips.append(f)

            #print(titles[0])
            #print(dates[0])
            #print(descrips[0])
            #print()
            del data[:]
            #i = i+1

        else:
            soup.find_all_next('div')

fmt = '{:<8}{:<25}{:<75}{}'


print(fmt.format('', 'Title', 'Date', 'Description'))
for i, (title, date, descrip) in enumerate(zip(titles, dates, descrips)):
    print(fmt.format(i, title, date, descrip))






#monthgrid 2875:17