from flask import Flask, send_file
from flask_restful import Api, Resource, abort, marshal_with, fields, reqparse
from flask_sqlalchemy import SQLAlchemy
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

get_args = reqparse.RequestParser()
#get_args.add_argument("iso2", type=str, help="ISO2 required", required=True)


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


class ItemList(Resource):
    def get(self):
        return {'items': country}


class Data(Resource):
    @marshal_with(resource_fields)
    def get(self):
        args = get_args.parse_args()
        print(args)
        c_iso2 = args["iso2"]
        print(c_iso2)
        result = DataModel.query.filter_by(iso2=c_iso2).first()
        if not result:
            abort(404, message="Country not found")
        return result


api.add_resource(Data, '/country')
api.add_resource(ItemList, '/countries')


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
