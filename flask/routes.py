from flask import request, jsonify
from app import app
import sqlite3

def add_trader_id_to_db(trader_id, deposit_value=None):
    with sqlite3.connect('ID.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO ID (id, deposit) VALUES (?, ?)', (trader_id, deposit_value))
        conn.commit()

def trader_id_exists(trader_id):
    with sqlite3.connect('ID.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM ID WHERE id = ?', (trader_id,))
        count = cursor.fetchone()[0]
    return count > 0

def update_deposit(trader_id, deposit_value):
    with sqlite3.connect('ID.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE ID SET deposit = ? WHERE id = ?', (deposit_value, trader_id))
        conn.commit()

@app.route('/', methods=['GET'])
def handle_get():
    trader_id = request.args.get('trader_id')
    sumdep = request.args.get('sumdep')

    if not trader_id:
        return jsonify({"message": "Отсутствует trader_id"}), 400

    try:
        trader_id = int(trader_id)
    except ValueError:
        return jsonify({"message": "trader_id должен быть целым числом"}), 400

    # Проверка: считается ли sumdep валидным (≠ 'false' и ≠ None/null)
    sumdep_valid = sumdep is not None and sumdep.lower() != 'false'

    if trader_id_exists(trader_id):
        if sumdep_valid:
            with sqlite3.connect('ID.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT deposit FROM ID WHERE id = ?', (trader_id,))
                current_deposit = cursor.fetchone()[0]
                if current_deposit is None:
                    update_deposit(trader_id, 1)
                    return jsonify({
                        "message": "Deposit обновлён на 1 для существующего trader_id",
                        "trader_id": trader_id
                    }), 200
                else:
                    return jsonify({
                        "message": "Deposit уже установлен, запрос проигнорирован",
                        "trader_id": trader_id
                    }), 200
        else:
            return jsonify({
                "message": "trader_id уже существует, sumdep отсутствует или false — запрос проигнорирован",
                "trader_id": trader_id
            }), 200
    else:
        if sumdep_valid:
            add_trader_id_to_db(trader_id, deposit_value=1)
            return jsonify({
                "message": "Новый trader_id добавлен с deposit = 1",
                "trader_id": trader_id
            }), 200
        else:
            add_trader_id_to_db(trader_id)  # deposit = None
            return jsonify({
                "message": "Новый trader_id добавлен с deposit = NULL",
                "trader_id": trader_id
            }), 200

