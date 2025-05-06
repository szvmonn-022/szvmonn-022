import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logging.info("🚀 Skrypt wystartował poprawnie")
import os
import logging
import requests
from bs4 import BeautifulSoup
import sqlite3
from requests.exceptions import RequestException
from apscheduler.schedulers.blocking import BlockingScheduler
from telegram import Bot
from telegram.error import TelegramError

# --------------------- LOGGING SETUP ---------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logging.info("🚀 Skrypt wystartował poprawnie")

# ---------------------- CONFIGURATION ----------------------
TOKEN   = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# ---------------------- SEARCH SETTINGS ----------------------
BASE_URL = 'https://www.olx.pl/oferty/q-iphone/'
SEARCH_PARAMS = {
    'search[filter_enum_item_condition][0]': 'new',
    'search[filter_enum_item_condition][1]': 'used',
    'search[filter_enum_item_condition][2]': 'not_specified',
    'search[region_id]': '18',    # Mazowieckie (Warszawa +20km)
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
    try:
        resp = requests.get(BASE_URL, params=SEARCH_PARAMS, timeout=10)
        resp.raise_for_status()
    except RequestException as e:
        logging.error(f"⚠️ Błąd pobierania OLX: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    offers = []
    for item in soup.select('div.offer-wrapper'):
        link_tag  = item.find('a', href=True)
        title_tag = item.find('strong')
        price_tag = item.find('p', class_='price')
        img_tag   = item.find('img')
        if not (link_tag and title_tag and price_tag and img_tag):
            continue

        url     = link_tag['href']
        title   = title_tag.get_text(strip=True)
        price   = price_tag.get_text(strip=True)
        img_url = img_tag.get('data-src') or img_tag.get('src')

        # Filtrujemy tylko modele 12–16 z wariantami
        models = [12,13,14,15,16]
        if any(f"iPhone {m}" in title for m in models) or \
           any(f"iPhone {m} Plus" in title for m in models) or \
           any(f"iPhone {m} Pro" in title for m in models) or \
           any(f"iPhone {m} Pro Max" in title for m in models):
            offers.append({
                'url': url,
                'title': title,
                'price': price,
                'img_url': img_url
            })
    return offers

# ---------------------- TELEGRAM TEST & NOTIFICATIONS ----------------------
def send_test_message():
    bot = Bot(token=TOKEN)
    try:
        bot.send_message(chat_id=CHAT_ID, text="✅ Test: bot wystartował i ma uprawnienia!")
        logging.info("✅ Wysłano testową wiadomość na Telegram")
    except TelegramError as e:
        logging.error(f"❌ Testowa wiadomość nie doszła: {e}")

def send_telegram(offer):
    bot = Bot(token=TOKEN)
    caption = f"{offer['title']}\n{offer['price']}\n{offer['url']}"
    try:
        bot.send_photo(chat_id=CHAT_ID, photo=offer['img_url'], caption=caption)
        logging.info(f"Wysłano ofertę: {offer['url']}")
    except TelegramError as e:
        logging.error(f"⚠️ Błąd przy wysyłaniu zdjęcia: {e}, wysyłam tekstem")
        bot.send_message(chat_id=CHAT_ID, text=caption)

# ---------------------- JOB FUNCTION ----------------------
def job():
    conn = init_db()
    c = conn.cursor()
    offers = fetch_offers()
    for offer in offers:
        c.execute('SELECT 1 FROM offers WHERE url=?', (offer['url'],))
        if not c.fetchone():
            send_telegram(offer)
            c.execute('INSERT INTO offers (url) VALUES (?)', (offer['url'],))
            conn.commit()
    conn.close()

# ---------------------- MAIN ----------------------
if __name__ == '__main__':
    # Wyślij najpierw testową wiadomość, żeby zweryfikować połączenie
    send_test_message()

    # Uruchom scheduler
    scheduler = BlockingScheduler()
    scheduler.add_job(job, 'interval', minutes=3)
    logging.info('🕒 Harmonogram ustawiony na co 3 minuty')
    job()  # pierwsze natychmiastowe wywołanie
    scheduler.start()
