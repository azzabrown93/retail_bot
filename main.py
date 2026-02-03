import requests
import time
import random
import os
from bs4 import BeautifulSoup

print("===== ELITE RETAIL RADAR + FLIP AI LIVE =====")

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")

MIN_PROFIT = 12
MIN_ROI = 0.30

SEEN = set()


#########################################
# EBAY TOKEN
#########################################

def get_ebay_token():
    url = "https://api.ebay.com/identity/v1/oauth2/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    response = requests.post(
        url,
        headers=headers,
        data=data,
        auth=(EBAY_CLIENT_ID, EBAY_CLIENT_SECRET)
    )

    return response.json()["access_token"]


TOKEN = get_ebay_token()


#########################################
# FLIP PROBABILITY ENGINE
#########################################

def flip_score(avg_price, sales_count, roi):

    score = 0

    # Demand
    if sales_count > 20:
        score += 3
    elif sales_count > 10:
        score += 2
    else:
        score += 1

    # ROI
    if roi > 0.8:
        score += 3
    elif roi > 0.5:
        score += 2
    else:
        score += 1

    # Sweet price band
    if 20 < avg_price < 120:
        score += 2

    #################################

    if score >= 7:
        return "🔥 VERY HIGH FLIP"
    elif score >= 5:
        return "⚡ HIGH FLIP"
    elif score >= 4:
        return "✅ SOLID"
    else:
        return "⚠️ SLOW"


#########################################
# EBAY SOLD SEARCH
#########################################

def ebay_sold_price(query):

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    params = {
        "q": query,
        "filter": "soldItemsOnly:true",
        "limit": 25
    }

    r = requests.get(url, headers=headers, params=params)

    data = r.json()

    prices = []

    if "itemSummaries" not in data:
        return None, 0

    for item in data["itemSummaries"]:
        try:
            prices.append(float(item["price"]["value"]))
        except:
            pass

    if not prices:
        return None, 0

    avg = sum(prices) / len(prices)

    return avg, len(prices)


#########################################
# DISCORD ALERT
#########################################

def send_alert(title, price, avg, profit, roi, url, score):

    message = f"""
🚨 **{score}**

**{title}**

💷 Store: £{price}
💰 eBay Avg: £{round(avg,2)}
📈 Profit: £{round(profit,2)}
📊 ROI: {round(roi*100)}%

{url}
"""

    requests.post(DISCORD_WEBHOOK, json={"content": message})


#########################################
# SCANNER
#########################################

def scan_site(site_name, url):

    print(f"Scanning {site_name}...")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=12)

    soup = BeautifulSoup(r.text, "lxml")

    products = soup.select(".product, .product-card, li")

    for product in products[:40]:

        text = product.get_text(" ", strip=True)

        price = None

        for word in text.split():
            if "£" in word:
                try:
                    price = float(word.replace("£", "").replace(",", ""))
                    break
                except:
                    pass

        if not price or price < 10:
            continue

        title = text[:120]

        if title in SEEN:
            continue

        avg, sales = ebay_sold_price(title)

        if not avg:
            continue

        profit = avg * 0.87 - price
        roi = profit / price

        if profit < MIN_PROFIT or roi < MIN_ROI:
            continue

        score = flip_score(avg, sales, roi)

        # only alert good flips
        if "SLOW" in score:
            continue

        send_alert(title, price, avg, profit, roi, url, score)

        SEEN.add(title)


#########################################
# SITES (NO AMAZON)
#########################################

SITES = [

    ("Smyths Toys",
     "https://www.smythstoys.com/uk/en-gb/search/?text=lego"),

    ("Argos",
     "https://www.argos.co.uk/search/lego/"),

    ("Currys",
     "https://www.currys.co.uk/search?q=nintendo"),

    ("Very",
     "https://www.very.co.uk/electricals/gaming/e/b/1223.end"),

    ("GAME",
     "https://www.game.co.uk/en/games/nintendo-switch-298559"),
]


#########################################
# HUMAN SLEEP
#########################################

def human_sleep():

    t = random.randint(120, 420)

    print(f"😴 Sleeping {t}s...")
    time.sleep(t)


#########################################
# MAIN LOOP
#########################################

while True:

    try:

        for site in SITES:
            scan_site(site[0], site[1])

        human_sleep()

    except Exception as e:

        print("Error:", e)

        time.sleep(60)
