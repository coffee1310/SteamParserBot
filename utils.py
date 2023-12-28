import datetime
import sqlite3
import time
import queue
import user_agent

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def get_item_information(link):
    options = Options()
    options.add_argument("--headless")
    options.add_argument(f"user-agent={user_agent.generate_user_agent()}")

    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(link)

    time.sleep(2)
    item_name = driver.find_element(By.CLASS_NAME, "hover_item_name").text.strip()
    item_price = driver.find_elements(By.CLASS_NAME, "market_commodity_orders_header_promote")[1].text.strip()

    driver.quit()
    return item_name, item_price

class Item:
    def __init__(self, items:list, user_id: str):
        self.items = items
        self.user_id = user_id
        self.result_queue = queue.Queue()

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
        connection = self.check_table()
        cursor = connection.cursor()
        for link in self.items:
            information = get_item_information(link)
            cursor.execute('''
                INSERT INTO items (link, item_name)
                VALUES (?, ?)
            ''', (link, information[0]))

            item_id = cursor.lastrowid
            print(information)
            cursor.execute('''
                INSERT INTO prices (user_id, item_id, item_price, date_changed)
                VALUES (?, ?, ?, ?)
            ''', (self.user_id, item_id, information[1], datetime.date.today()))
            print("Данные внесены")

        connection.commit()
        connection.close()