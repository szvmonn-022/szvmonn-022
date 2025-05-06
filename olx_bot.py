import os
import requests
from bs4 import BeautifulSoup
import sqlite3
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from telegram import Bot
from telegram.error import TelegramError

# ---------------------- CONFIGURATION ----------------------
# Token and Chat ID are read from environment variables
TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# ---------------------- SEARCH SETTINGS ----------------------
BASE_URL = 'https://www.olx.pl/oferty/q-iphone/'
SEARCH_PARAMS = {
    'search[filter_enum_item_condition][0]': 'new',
    'search[filter_enum_item_condition][1]': 'used',
    'search[filter_enum_item_condition][2]': 'not_specified',
    'search[region_id]': '18',  # Mazowieckie (Warszawa +20km)
    'search[page]': '1'
}

# ---------------------- DATABASE SETUP ----------------------
def init_db():
    conn = sqlite3.connect('olx_offers.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE
        )
    ''')
    conn.commit()
    return conn

# ---------------------- SCRAPING LOGIC ----------------------
def fetch_offers():
    response = requests.get(BASE_URL, params=SEARCH_PARAMS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    offers = []
    for item in soup.select('div.offer-wrapper'):
        link_tag = item.find('a', href=True)
        if not link_tag:
            continue
        url = link_tag['href']
        title_tag = item.find('strong')
        price_tag = item.find('p', class_='price')
        img_tag = item.find('img')
        if not (title_tag and price_tag and img_tag):
            continue
        title = title_tag.get_text(strip=True)
        price = price_tag.get_text(strip=True)
        img_url = img_tag.get('data-src') or img_tag.get('src')
        # Filter models 12-16 variants
        models = [12, 13, 14, 15, 16]
        if any(f"iPhone {m}" in title for m in models) or            any(f"iPhone {m} Plus" in title for m in models) or            any(f"iPhone {m} Pro" in title for m in models) or            any(f"iPhone {m} Pro Max" in title for m in models):
            offers.append({
                'url': url,
                'title': title,
                'price': price,
                'img_url': img_url
            })
    return offers

# ---------------------- TELEGRAM NOTIFICATIONS ----------------------
def send_telegram(offer):
    bot = Bot(token=TOKEN)
    caption = f"{offer['title']}\n{offer['price']}\n{offer['url']}"
    try:
        bot.send_photo(chat_id=CHAT_ID, photo=offer['img_url'], caption=caption)
    except TelegramError:
        bot.send_message(chat_id=CHAT_ID, text=caption)

# ---------------------- JOB FUNCTION ----------------------
def job():
    conn = init_db()
    c = conn.cursor()
    offers = fetch_offers()
    for offer in offers:
        c.execute('SELECT 1 FROM offers WHERE url=?', (offer['url'],))
        if not c.fetchone():
            logging.info(f"New offer: {offer['url']}")
            send_telegram(offer)
            c.execute('INSERT INTO offers (url) VALUES (?)', (offer['url'],))
            conn.commit()
    conn.close()

# ---------------------- MAIN ----------------------
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
    scheduler = BlockingScheduler()
    scheduler.add_job(job, 'interval', minutes=3)
    logging.info('Starting OLX bot...')
    job()  # initial run
    scheduler.start()
