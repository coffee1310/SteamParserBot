import telebot
import datetime
import sqlite3
import time
import queue
import user_agent
import threading
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_item_information(link):
    options = Options()
    #options.add_argument("--headless")
    #options.add_argument(f"--proxy-server=45.11.6.117:54389")

    options.add_argument(f"user-agent={user_agent.generate_user_agent()}")
    options.add_argument(f"--window-size={random.randint(1000, 1900)},{random.randint(1000, 1900)}")
    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(str(random.randint(100, 1900)), str(random.randint(100, 1900)))
    driver.get(link)
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "market_commodity_orders_header_promote")))
    try:
        item_name = driver.find_element(By.CLASS_NAME, "hover_item_name").text.strip()
        item_price = driver.find_elements(By.CLASS_NAME, "market_commodity_orders_header_promote")[1].text.strip()
    except Exception as exp:
        print(exp)
    driver.quit()
    return item_name, item_price

def get_items(user_id):
    connection = sqlite3.Connection("items.db")
    cursor = connection.cursor()
    cursor.execute("SELECT item_id FROM prices WHERE user_id = ?", (user_id,))
    results = cursor.fetchall()
    items = []

    for i in results:
        cursor.execute("SELECT item_name FROM items WHERE id = ?", i)
        items.append(*cursor.fetchall()[0])

    return items

def get_item_info(user_id, item_name):
    connection = sqlite3.Connection("items.db")
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM items WHERE item_name = ?", (item_name,))
    results = cursor.fetchall()
    cursor.execute("SELECT item_price, date_changed FROM prices WHERE item_id = ?", results[0])
    results = cursor.fetchall()

    return results


class Item:
    def __init__(self, items:list, user_id: str):
        self.items = items
        self.user_id = user_id
        self.result_queue = queue.Queue()

    def process_link(self):
        time.sleep(3)
        while True:
            link = self.link_queue.get()
            if link is None:
                break
            item_info = get_item_information(link)
            self.result_queue.put(item_info)
            self.link_queue.task_done()
    def check_table(self):
        connection = sqlite3.Connection("items.db")
        cursor = connection.cursor()
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        link TEXT NOT NULL,
                        item_name TEXT NOT NULL
                    )
                ''')
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS prices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        item_id INTEGER NOT NULL,
                        item_price FLOAT NOT NULL,
                        date_changed DATE NOT NULL,
                        FOREIGN KEY (item_id) REFERENCES items(id)
                    )
                ''')
        return connection

    def write_item(self):
        start = time.time()
        connection = sqlite3.Connection("items.db")
        cursor = connection.cursor()

        self.link_queue = queue.Queue()
        for link in self.items:
            if (link == '' and link ==' '):
                continue
            print(link)
            self.link_queue.put(link)

        threads = []
        num_threads = 3
        if len(self.items) < 3:
            num_threads = len(self.items)

        for i in range(num_threads):
            thread = threading.Thread(target=self.process_link)
            thread.start()
            threads.append(thread)

        self.link_queue.join()

        for i in range(num_threads):
            self.link_queue.put(None)

        for thread in threads:
            thread.join()

        result_items = []
        while not self.result_queue.empty():
            result_items.append(self.result_queue.get())
        for item in result_items:
            cursor.execute('''
                            INSERT INTO items (link, item_name)
                            VALUES (?, ?)
                        ''', (link, item[0]))
            print(item[0], item[1])

            item_id = cursor.lastrowid
            cursor.execute('''
                            INSERT INTO prices (user_id, item_id, item_price, date_changed)
                            VALUES (?, ?, ?, ?)
                        ''', (self.user_id, item_id, item[1], datetime.date.today()))
        connection.commit()
        connection.close()

        print(time.time() - start)