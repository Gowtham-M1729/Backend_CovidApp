from flask import Flask, send_file, jsonify
from flask_restful import Api, Resource, abort, marshal_with, fields, reqparse
from flask_sqlalchemy import SQLAlchemy, inspect
import requests
import json
import matplotlib.pyplot as plt
import threading
import schedule
import time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

parser = reqparse.RequestParser()
parser.add_argument('price',
                    type=float,
                    required=True,
                    help="This field cannot be left blank!"
                    )


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
        return f"Data(name = {country},iso2={iso2},slug={slug} ,newconfiremd = {newConfirmed}, newdeaths = {newDeaths}, newrecovered = {newRecovered},totalconfirmed={totalConfirmed},totalrecovered={totalRecovered},totaldeaths={totalDeaths},active = {active})"

    def dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


resource_fields = {
    'iso2': fields.String,
    'country': fields.String,
    'slug': fields.String,
    'newConfirmed': fields.Integer,
    'totalConfirmed': fields.Integer,
    'totalDaeths': fields.Integer,
    'newDeaths': fields.Integer,
    'totalRecovered': fields.Integer,
    'newRecovered': fields.Integer,
    'active': fields.Integer

}


def updateDatabase():

    print("Updating database ....")
    BASE = "https://api.covid19api.com/total/country/"
    lst_countrysummary = (requests.get(
        "https://api.covid19api.com/summary")).json()
    lst = lst_countrysummary["Countries"]
    countries = sorted(lst, key=lambda c: c["NewConfirmed"])
    globaldata = lst_countrysummary['Global']

    for i in lst:
        (country, countrycode, slug, newconfirmed, totalconfirmed, newdeaths, totaldeaths, newrecovered, totalrecovered,
         date) = i['Country'], i['CountryCode'], i['Slug'], i['NewConfirmed'], i['TotalConfirmed'], i['NewDeaths'], i['TotalDeaths'], i['NewRecovered'], i['TotalRecovered'], i['Date']

        countries_info = requests.get(BASE + countrycode).json()
        activeCases = countries_info[-1]['Active'] - \
            countries_info[-2]['Active']

        c_data = DataModel(iso2=countrycode, country=country, slug=slug, newConfirmed=newconfirmed, newDeaths=newdeaths, newRecovered=newrecovered, totalConfirmed=totalconfirmed,
                           totalRecovered=totalrecovered, totalDeaths=totaldeaths, active=activeCases)
        db.session.add(c_data)

        print("Updated " + country)
        db.session.commit()

    print("Update complete ...")


@app.route('/reset')
def reset():
    db.drop_all()
    db.create_all()
    return "Done"

# routes


# @app.route('/country')
# def index():
#     try:
#         socks = DataModel.query.filter_by(
#             iso2='IN').order_by(DataModel.country).all()
#         sock_text = '<ul>'
#         for sock in socks:
#             sock_text += '<li>' + sock.country + \
#                 ', ' + str(sock.active) + '</li>'
#         sock_text += '</ul>'
#         return sock_text
#     except Exception as e:
#         # e holds description of the error
#         error_text = "<p>The error:<br>" + str(e) + "</p>"
#         hed = '<h1>Something is broken.</h1>'
#         return hed + error_text

@app.route('/country')
def index():
    try:
        data = DataModel.query.all()
        # print(data)
        return jsonify([x.dict() for x in data])
        for d in data:
            print(d.json())
    except Exception as e:
        return e
    return ""


@app.route('/country<String Country Code>')
def countryinfo():
    try:
        socks = DataModel.query.filter_by(
            iso2='IN').order_by(DataModel.country).all()
        sock_text = '<ul>'
        for sock in socks:
            sock_text += '<li>' + sock.country + \
                ', ' + str(sock.active) + '</li>'
        sock_text += '</ul>'
        return sock_text
    except Exception as e:
        # e holds description of the error
        error_text = "<p>The error:<br>" + str(e) + "</p>"
        hed = '<h1>Something is broken.</h1>'
        return hed + error_text


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
