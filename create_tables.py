import sqlite3
import requests
from flask import Flask


lst_countrtinfo = requests.get("https://api.covid19api.com/countries")
lst_c = lst_countrtinfo.json()
lst_countrysummary = (requests.get(
    "https://api.covid19api.com/summary")).json()
lst = lst_countrysummary["Countries"]

connection = sqlite3.connect('data.db')
cursor = connection.cursor()

# instead of specifying id each time we create a user , we can use INTEGER PRIMARY KEY wch automatically increments id
create_table = "CREATE TABLE IF NOT EXISTS countrysummary(ID INTEGER PRIMARY KEY AUTOINCREMENT,country text, ISO text, slug text, newconfirmed int, totalconfirmed int, newdeaths int, totaldeaths int, newrecovered int, totalrecovered int, date text)"
cursor.execute(create_table)

create_table = "CREATE TABLE IF NOT EXISTS countries(id INTEGER PRIMARY KEY,country text, slug text, iso2 text)"
cursor.execute(create_table)

for i in lst_c:
    country = i['Country']
    slug = i['Slug']
    iso2 = i['ISO2']
    params = (country, slug, iso2)
    cursor.execute("INSERT INTO countries VALUES (NULL,?,?,?)", params)

# country summary
for i in lst:
    country, ISO, slug, newconfirmed, totalconfirmed, newdeaths, totaldeaths, newrecovered, totalrecovered, date = i['Country'], i[
        'CountryCode'], i['Slug'], i['NewConfirmed'], i['TotalConfirmed'], i['NewDeaths'], i['TotalDeaths'], i['NewRecovered'], i['TotalRecovered'], i['Date']
    params = (country, ISO, slug, newconfirmed, totalconfirmed,
              newdeaths, totaldeaths, newrecovered, totalrecovered, date)
    # print(params)
    cursor.execute(
        "INSERT INTO countrysummary VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", params)
connection.commit()

connection.close()
