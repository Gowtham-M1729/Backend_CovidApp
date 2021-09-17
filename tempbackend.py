from flask import Flask, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy, inspect
import requests
import json
import threading
from requests.sessions import session
import schedule
import time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


class DataModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    iso2 = db.Column(db.String, nullable=False)
    country = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False)
    newConfirmed = db.Column(db.Integer, nullable=False)
    newDeaths = db.Column(db.Integer, nullable=False)
    newRecovered = db.Column(db.Integer, nullable=False)
    totalConfirmed = db.Column(db.Integer, nullable=False)
    totalDeaths = db.Column(db.Integer, nullable=False)
    totalRecovered = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Data(name = {self.country},iso2={self.iso2},slug={self.slug} ,newconfiremd = {self.newConfirmed}, newdeaths = {self.newDeaths}, newrecovered = {self.newRecovered},totalconfirmed={self.totalConfirmed},totalrecovered={self.totalRecovered},totaldeaths={self.totalDeaths},active = {self.active})"

    def dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


def updateDatabase():

    print("Updating database ....")
    BASE = "https://api.covid19api.com/total/country/"
    lst_countrysummary = (requests.get(
        "https://api.covid19api.com/summary")).json()
    lst = lst_countrysummary["Countries"]
    #countries = sorted(lst, key=lambda c: c["NewConfirmed"])
    globaldata = lst_countrysummary['Global']

    for i in lst:
        (country, countrycode, slug, newconfirmed, totalconfirmed, newdeaths, totaldeaths, newrecovered, totalrecovered,
         date) = i['Country'], i['CountryCode'], i['Slug'], i['NewConfirmed'], i['TotalConfirmed'], i['NewDeaths'], i['TotalDeaths'], i['NewRecovered'], i['TotalRecovered'], i['Date']

        countries_info = requests.get(BASE + countrycode).json()
        # print(countries_info)
        activeCases = countries_info[-1]['Active'] - \
            countries_info[-2]['Active']

        c_data = DataModel(iso2=countrycode, country=country, slug=slug, newConfirmed=newconfirmed, newDeaths=newdeaths, newRecovered=newrecovered, totalConfirmed=totalconfirmed,
                           totalRecovered=totalrecovered, totalDeaths=totaldeaths, active=activeCases)
        db.session.add(c_data)

        print("Updated " + country)
        db.session.commit()
        # time.sleep(1)

    print("Update complete ...")


@app.route('/reset')
def reset():
    db.drop_all()
    db.create_all()
    return "Done"


@app.route('/countryList')
def countrylist():
    try:
        lst = []
        result = list(DataModel.query.with_entities(DataModel.country))
        for i in result:
            lst.append(i[0])
        return json.dumps(lst)
    except Exception as e:
        return str(e)


@app.route('/country')
def index():
    try:
        data = DataModel.query.all()
        return jsonify([x.dict() for x in data])
    except Exception as e:
        return str(e)


@app.route('/country/<string:name>')
def countryinfo(name):
    try:
        data = DataModel.query.filter(DataModel.country == name).first()
        return(jsonify(data.dict()))
    except:
        return jsonify({'message': 'Country info not found'})


if __name__ == "__main__":

    db.create_all()

    thread = threading.Thread(target=updateDatabase)
    thread.start()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=updateDatabase, trigger="interval", days=1)
    scheduler.start()

    app.run(debug=True, use_reloader=False,
            port=os.getenv("PORT"), host="0.0.0.0")
    atexit.register(lambda: scheduler.shutdown())
