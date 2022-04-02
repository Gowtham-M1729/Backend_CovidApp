from enum import unique
from flask import Flask, send_file, jsonify, render_template
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
    country = db.Column(db.String(100), nullable=False, unique=True)
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


class Global(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(100), nullable=False)
    newConfirmed = db.Column(db.Integer, nullable=False)
    newDeaths = db.Column(db.Integer, nullable=False)
    newRecovered = db.Column(db.Integer, nullable=False)
    totalConfirmed = db.Column(db.Integer, nullable=False)
    totalDeaths = db.Column(db.Integer, nullable=False)
    totalRecovered = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Data(name = {self.country},newconfiremd = {self.newConfirmed}, newdeaths = {self.newDeaths}, newrecovered = {self.newRecovered},totalconfirmed={self.totalConfirmed},totalrecovered={self.totalRecovered},totaldeaths={self.totalDeaths},active = {self.active})"

    def dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


def updateDatabase():
    db.drop_all()
    db.create_all()
    print("Updating database ....")
    BASE = "https://api.covid19api.com/total/country/"
    lst_countrysummary = (requests.get(
        "https://api.covid19api.com/summary")).json()
    lst = lst_countrysummary["Countries"]
    countries = sorted(lst, key=lambda c: c["NewConfirmed"])
    globalactivecase = 0
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
        globalactivecase += activeCases

        print("Updated " + country)
        db.session.commit()
        time.sleep(1)

    globaldata = lst_countrysummary['Global']

    (country, newconfirmed, totalconfirmed, newdeaths, totaldeaths, newrecovered, totalrecovered,
     date) = "Global", globaldata['NewConfirmed'], globaldata['TotalConfirmed'], globaldata['NewDeaths'], globaldata['TotalDeaths'], globaldata['NewRecovered'], globaldata['TotalRecovered'], globaldata['Date']

    c_data = Global(country=country, newConfirmed=newconfirmed, newDeaths=newdeaths, newRecovered=newrecovered, totalConfirmed=totalconfirmed,
                    totalRecovered=totalrecovered, totalDeaths=totaldeaths, active=globalactivecase)
    db.session.add(c_data)
    db.session.commit()
    print("Updated Global Data")

    print("Update complete ...")


@ app.route('/reset')
def reset():
    db.drop_all()
    db.create_all()
    return "Done"


@app.route('/')
def home():
    return render_template('index.html')


@ app.route('/Global')
def globalinfo():
    try:
        data = (Global.query.filter_by(country='Global').first())
        return jsonify(data.dict())
    except:
        return jsonify({'message': 'Global information not found'})


@ app.route('/countryList')
def countrylist():
    try:
        lst = []
        result = list(DataModel.query.with_entities(DataModel.country))
        for i in result:
            lst.append(i[0])
        return jsonify(lst)
    except Exception as e:
        return str(e)


@ app.route('/country')
def index():
    try:
        data = DataModel.query.all()
        return jsonify([x.dict() for x in data])
    except Exception as e:
        return str(e)


@ app.route('/country/<string:name>')
def countryinfo(name):
    try:
        data = DataModel.query.filter(DataModel.country == name).first()
        return(jsonify(data.dict()))
    except:
        return jsonify({'message': 'Country info not found'})


@app.route('/MostCases')
def MostCases():
    try:
        data = DataModel.query.order_by(DataModel.active).all()
        l = [x.dict() for x in data][::-1][:5]
        print(l)
        mostcase = []
        for cnt in l:
            mostcase.append(cnt["country"])
        return jsonify(mostcase)
    except:
        return jsonify({'message': 'Information yet to be Updated'})


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
