import feedparser
from flask import Flask
from flask import render_template
from flask import request
import json
import urllib
from urllib.parse import quote
from urllib.request import urlopen
import datetime
from flask import make_response


app = Flask(__name__)



rss_feeds = {
    "lapresse": "http://lapresse.ca/rss/225.xml",
    "journal": "https://journaldemontreal.com/rss.xml",
}

DEFAULTS = {
            "publication": "lapresse",
            "city": "Montréal,CA",
            "currency_from": "CAD",
            "currency_to": "USD"
}

WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather?" \
              "q={}&units=metric&APPID=6bb59c2cefa0663dcf00e9f251e11d0b"

CURRENCY_URL = "https://openexchangerates.org/api/latest.json?" \
               "app_id=d8bc2e4ee0a54c58a1557c80e798e778"


def get_value_with_fallback(key):
    if request.args.get(key):
        return request.args.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)
    return DEFAULTS[key]


@app.route("/")
def home():
    publication = get_value_with_fallback("publication")
    articles = get_news(publication)

    city = get_value_with_fallback("city")
    weather = get_weather(city)

    currency_from = get_value_with_fallback("currency_from")
    currency_to = get_value_with_fallback("currency_to")
    rate, currencies = get_rate(currency_from, currency_to)

    response = make_response(render_template("home.html", articles=articles,
                                        weather=weather,
                                        currency_from=currency_from,
                                        currency_to=currency_to,
                                        rate=rate,
                                        currencies=sorted(currencies)))
    expires = datetime.datetime.now() + datetime.timedelta(days=365)
    response.set_cookie("publication", publication, expires=expires)
    response.set_cookie("city", city, expires=expires)
    response.set_cookie("currency_from", currency_from, expires=expires)
    return response


@app.route("/")
def get_news(query):
    if not query or query.lower() not in rss_feeds:
        publication = DEFAULTS["publication"]
    else:
        publication = query.lower()
    feed = feedparser.parse(rss_feeds[publication])
    return feed["entries"]


def get_weather(query):
    query = urllib.parse.quote(query)
    url = WEATHER_URL.format(query)
    data = urlopen(url)         # removed .read()
    parsed = json.load(data)
    weather = None
    if parsed.get("weather"):
        weather = {
                   "description": parsed["weather"][0]["description"],
                   "temperature": parsed["main"]["temp"],
                   "city": parsed["name"],
                   "country": parsed["sys"]["country"]
        }
    return weather


def get_rate(frm, to):
    all_currency = urlopen(CURRENCY_URL).read()
    parsed = json.loads(all_currency).get("rates")
    frm_rate = parsed.get(frm.upper())
    to_rate = parsed.get(to.upper())
    return (to_rate / frm_rate, parsed.keys())



if __name__ == '__main__':
    app.run(port=5000, debug=True)





