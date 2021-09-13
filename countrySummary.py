import requests
import json

summary = (requests.get("https://api.covid19api.com/summary")).json()
lst = summary["Countries"]
globaldata = summary['Global']
for i, j in globaldata.items():
    print(i, j)
print(globaldata)
for i in lst:
    (country, countrycode, slug, newconfirmed, totalconfirmed, newdeaths, totaldeaths, newrecovered, totalrecovered,
     date) = i['Country'], i['CountryCode'], i['Slug'], i['NewConfirmed'], i['TotalConfirmed'], i['NewDeaths'], i['TotalDeaths'], i['NewRecovered'], i['TotalRecovered'], i['Date']
countrySummary = summary['Countries']
countries = sorted(countrySummary, key=lambda c: c["NewConfirmed"])
print(len(countries))
lst = countries[188:192]
for i in lst:
    print(i)
