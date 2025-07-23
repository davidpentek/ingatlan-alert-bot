import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import ssl
from datetime import datetime
import json
import os
from flask import Flask, request

# Flask setup to respond to UptimeRobot
app = Flask(__name__)

SEARCH_URL = "https://ingatlan.com/lista/kiado+lakas+45-m2-felett+wc-kulon+1-emelet-felett+van-legkondi+csak-kepes+tegla-epitesu-lakas+havi-280-ezer-Ft-ig+i-ker+ii-ker+iii-ker+iv-ker+ix-ker+v-ker+vi-ker+vii-ker+viii-ker+x-ker+xi-ker+xiii-ker"

EMAIL_TO = ["david@davidpentek.com"]
EMAIL_FROM = "albi2025automation@gmail.com"
EMAIL_PASS = "dejq jbws zxyc ynud"

SEEN_FILE = "seen_listings.json"

def load_seen_ids():
    if not os.path.exists(SEEN_FILE):
        print("[INFO] First run — creating seen_listings.json")
        with open(SEEN_FILE, "w") as f:
            json.dump([], f)
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(json.load(f))

def save_seen_ids(ids):
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(list(ids), f)
        print("[INFO] Successfully saved seen listings.")
    except Exception as e:
        print(f"[ERROR] Failed to save seen_listings.json: {e}")

def get_listings():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import time

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(SEARCH_URL)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    listings = []
    for item in soup.select("a.listing__link"):
        url = item["href"]
        if not url.startswith("http"):
            url = "https://ingatlan.com" + url
        listing_id = url.strip("/").split("/")[-1]
        title = item.get("title", "Ingatlan hirdetés")
        listings.append({
            "id": listing_id,
            "title": title,
            "url": url
        })

    print(f"[INFO] Found {len(listings)} listings")
    return listings

def send_email(listings):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    body = "\n\n".join([f"{l['title']}\n{l['url']}" for l in listings])
    msg = MIMEText(body)
    msg["Subject"] = f"🏠 {len(listings)} új ingatlan – {now}"
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_FROM, EMAIL_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print("[INFO] Email sent successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")

@app.route("/", methods=["GET"])
def trigger_scraper():
    print("[INFO] Triggered by UptimeRobot")

    seen_ids = load_seen_ids()
    listings = get_listings()
    new_listings = [l for l in listings if l["id"] not in seen_ids]

    if new_listings:
        send_email(new_listings)
        seen_ids.update([l["id"] for l in new_listings])
        save_seen_ids(seen_ids)
    else:
        print("[INFO] No new listings found")

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
