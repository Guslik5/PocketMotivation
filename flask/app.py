import logging
from flask import Flask
import sqlite3

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

def init_db():
    with sqlite3.connect('ID.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ID (
                id INTEGER PRIMARY KEY,
                deposit TEXT
            )
        ''')
        conn.commit()
    app.logger.info("База данных и таблица успешно созданы.")

init_db()

from routes import *

if __name__ == '__main__':
    app.run(debug=True)
