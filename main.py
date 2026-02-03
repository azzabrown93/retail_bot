import requests
import time
import random
import os
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

DISCORD = os.getenv("DISCORD_WEBHOOK")
EBAY = os.getenv("EBAY_TOKEN")

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-GB,en;q=0.9"
})

SEEN = {}

############################
# DISCORD
############################

def ping(msg):
    try:
        requests.post(DISCORD, json={"content": msg}, timeout=8)
    except:
        print("Discord failed")

ping("🚀 **ELITE AUTO-SNIPER LIVE** — Hunting flips now.")

############################
# EBAY SOLD DATA
############################

def ebay_avg(title):

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    headers = {
        "Authorization": f"Bearer {EBAY}"
    }

    params = {
        "q": title,
        "filter": "soldItemsOnly:true",
        "limit": 5
    }

    try:
        r = session.get(url, headers=headers, params=params, timeout=6)
        data = r.json()

        prices = [
            float(i["price"]["value"])
            for i in data.get("itemSummaries", [])
        ]

        if prices:
            return sum(prices) / len(prices)

    except:
        return None


############################
# FLIP AI
############################

def score(retail, ebay):

    profit = ebay - retail
    margin = profit / retail * 100

    s = 0

    if profit > 15: s += 25
    if profit > 30: s += 25
    if margin > 25: s += 20
    if margin > 40: s += 20
    if ebay > 50: s += 10

    return s


def evaluate(title, price, link, store):

    key = f"{title}-{price}"

    if key in SEEN:
        return

    ebay = ebay_avg(title)

    if not ebay:
        return

    flip = score(price, ebay)

    if flip < 60:
        return

    profit = ebay - price
    margin = profit / price * 100

    SEEN[key] = True

    ping(f"""
🔥 **FLIP SNIPED — SCORE {flip}/100**

Store: {store}

{title}

Retail: £{price}
eBay Avg: £{round(ebay,2)}

Profit: £{round(profit,2)}
Margin: {round(margin)}%

{link}
""")


############################
# SCRAPERS
############################

def smyths():

    print("Scanning Smyths")

    url = "https://www.smythstoys.com/uk/en-gb/search/?text=pokemon"

    try:
        r = session.get(url, timeout=8)
        soup = BeautifulSoup(r.text,"html.parser")

        items = soup.select(".product-card")[:6]

        for i in items:

            title = i.select_one(".product-card__title").text.strip()
            price = float(i.select_one(".product-card__price").text.replace("£",""))
            link = "https://www.smythstoys.com" + i.select_one("a")["href"]

            evaluate(title,price,link,"Smyths")

    except:
        print("Smyths blocked")


def argos():

    print("Scanning Argos")

    url = "https://www.argos.co.uk/search/pokemon/"

    try:
        r = session.get(url, timeout=8)
        soup = BeautifulSoup(r.text,"html.parser")

        items = soup.select("div[data-test='component-product-card']")[:6]

        for i in items:

            title = i.select_one("h3").text.strip()
            price = float(i.select_one("[data-test='product-price']").text.replace("£",""))
            link = "https://argos.co.uk" + i.select_one("a")["href"]

            evaluate(title,price,link,"Argos")

    except:
        print("Argos blocked")


def lego_currys():

    print("Scanning Currys Lego")

    url = "https://www.currys.co.uk/search?q=lego"

    try:
        r = session.get(url, timeout=8)
        soup = BeautifulSoup(r.text,"html.parser")

        items = soup.select(".product")[:6]

        for i in items:

            title = i.select_one(".description").text.strip()
            price = float(i.select_one(".price").text.replace("£",""))
            link = "https://currys.co.uk" + i.select_one("a")["href"]

            evaluate(title,price,link,"Currys")

    except:
        print("Currys blocked")


############################
# ENGINE
############################

stores = [
    smyths,
    argos,
    lego_currys
]

while True:

    with ThreadPoolExecutor(max_workers=3) as exe:
        exe.map(lambda f: f(), stores)

    sleep = random.randint(45,90)

    print(f"Sleeping {sleep}s")
    time.sleep(sleep)
