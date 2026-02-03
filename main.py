import requests
from bs4 import BeautifulSoup
import time
import random
import os

print("===== RETAIL RADAR BOT LIVE =====")

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")

MIN_PROFIT = 20
MIN_ROI = 0.30
EBAY_FEE = 0.13

SEEN = set()

########################################
# DISCORD
########################################

def alert(msg):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": msg})
    except:
        print("Discord error")


########################################
# EBAY TOKEN
########################################

def get_token():

    url = "https://api.ebay.com/identity/v1/oauth2/token"

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    res = requests.post(
        url,
        data=data,
        headers={"Content-Type":"application/x-www-form-urlencoded"},
        auth=(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET)
    )

    return res.json()["access_token"]

TOKEN = get_token()


########################################
# EBAY SOLD CHECK
########################################

def ebay_price(title):

    headers = {"Authorization": f"Bearer {TOKEN}"}

    params = {
        "q": title,
        "filter": "soldItemsOnly:true",
        "limit": 6
    }

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    try:
        r = requests.get(url, headers=headers, params=params).json()

        prices = [
            float(item["price"]["value"])
            for item in r.get("itemSummaries", [])
        ]

        if prices:
            return sum(prices)/len(prices)

    except:
        pass

    return None


########################################
# PROFIT ENGINE
########################################

def analyze(title, price, link):

    if title in SEEN:
        return

    sold = ebay_price(title)

    if not sold:
        print(f"No sold data: {title[:40]}")
        return

    profit = sold*(1-EBAY_FEE) - price
    roi = profit / price

    print(f"{title[:45]} | Profit £{round(profit,2)}")

    if profit > MIN_PROFIT and roi > MIN_ROI:

        SEEN.add(title)

        msg = f"""
🔥 **HIGH PROFIT FLIP**

{title}

💷 Retail: £{price}
📈 Sold Avg: £{round(sold,2)}
💵 Profit: £{round(profit,2)}
📊 ROI: {round(roi*100)}%

👉 {link}
"""

        alert(msg)


########################################
# STORE SCANNERS
########################################

HEADERS = {"User-Agent":"Mozilla/5.0"}


def scan_argos():

    print("Scanning Argos...")

    url = "https://www.argos.co.uk/search/lego/"

    soup = BeautifulSoup(requests.get(url,headers=HEADERS).text,"lxml")

    items = soup.select(".ProductCardstyles__Title-h52kot-12")

    prices = soup.select(".ProductCardstyles__PriceText-h52kot-14")

    for title,price in zip(items,prices):

        try:
            title = title.text.strip()
            price = float(price.text.replace("£",""))

            analyze(title,price,url)

        except:
            continue


def scan_smyths():

    print("Scanning Smyths...")

    url = "https://www.smythstoys.com/uk/en-gb/search/?text=lego"

    soup = BeautifulSoup(requests.get(url,headers=HEADERS).text,"lxml")

    cards = soup.select(".product-card")

    for c in cards[:12]:

        try:
            title = c.select_one(".product-card__title").text.strip()
            price = float(c.select_one(".price").text.replace("£",""))
            link = "https://www.smythstoys.com" + c.find("a")["href"]

            analyze(title,price,link)

        except:
            continue


def scan_currys():

    print("Scanning Currys...")

    url = "https://www.currys.co.uk/search?q=lego"

    soup = BeautifulSoup(requests.get(url,headers=HEADERS).text,"lxml")

    cards = soup.select(".product")

    for c in cards[:10]:

        try:
            title = c.select_one(".productTitle").text.strip()
            price = float(c.select_one(".price").text.replace("£",""))
            link = "https://www.currys.co.uk" + c.find("a")["href"]

            analyze(title,price,link)

        except:
            continue


########################################
# LOOP
########################################

def human_sleep():

    t = random.randint(180,420)

    print(f"Sleeping {t}s\n")

    time.sleep(t)


while True:

    try:

        scan_argos()
        scan_smyths()
        scan_currys()

        human_sleep()

    except Exception as e:

        print("ERROR:",e)
        time.sleep(120)
