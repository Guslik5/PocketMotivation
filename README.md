# PocketMotivation

Telegram-бот с воронкой для партнёрской программы **Pocket Option**. Бот проводит пользователя по шагам: подписка на канал → регистрация по реферальной ссылке → проверка Trader ID → проверка первого депозита → доступ к Web App с сигналами. Факты регистрации и депозита бот берёт из постбэков Pocket Option, которые принимает отдельный Flask-сервис.

## Возможности

**Для пользователей**

- Выбор языка: русский, английский, узбекский (смену языка можно сделать в любой момент).
- Обязательная подписка на Telegram-канал перед началом работы.
- Пошаговая воронка:
  1. **Регистрация.** Бот выдаёт реферальную ссылку и промокод, пользователь присылает свой Trader ID.
  2. **Проверка ID.** ID ищется в базе постбэков. Если его там нет, бот просит зарегистрироваться заново по ссылке.
  3. **Депозит.** По кнопке «Проверить» бот смотрит, пришёл ли постбэк о первом депозите.
  4. **Сигналы.** После депозита открывается кнопка Web App с сигналами.
- Инструкция и кнопка связи с поддержкой.

**Для администратора** (`/admin`)

- Рассылка любого сообщения всем пользователям с предпросмотром и подтверждением.
- Статистика: всего пользователей, прошедших верификацию, сделавших депозит.
- Смена реферальной ссылки и промокода прямо из бота, без перезапуска.
- Уведомление о каждом новом нажатии `/start` (username, ID, имя, время).

## Как это работает

```
Pocket Option ──постбэк──▶ Flask (:8000) ──▶ flask/ID.db
                                                 ▲
                                                 │ чтение
Пользователь ◀──▶ Telegram-бот (aiogram) ────────┘
                         │
                         └──▶ bot/database/user.db (пользователи, ссылка, промокод)
```

- **Flask-сервис** принимает `GET /?trader_id=...&sumdep=...`. Новый `trader_id` записывается в `ID.db`; если `sumdep` пришёл и не равен `false`, у записи ставится отметка о депозите.
- **Бот** читает `ID.db` по пути `DB_PATH`, чтобы проверить ID и депозит, и хранит свои данные в `bot/database/user.db`.

## Стек

- Python 3.10+
- [aiogram 3.12](https://docs.aiogram.dev/) и aiosqlite для бота
- Flask 3.1 и gunicorn для приёма постбэков
- SQLite

## Структура проекта

```
bot/
├── main.py              # точка входа бота
├── config.py            # настройки (токен, канал, админ, пути)
├── handlers/
│   ├── client.py        # пользовательская воронка
│   └── admin.py         # админ-панель
├── keyboards/           # inline-клавиатуры
├── database/db.py       # работа с user.db
├── other/
│   ├── filters.py       # проверка подписки и регистрации
│   └── languages.py     # тексты на ru / en / uz
├── image/               # картинки для сообщений
└── req.txt              # зависимости бота
flask/
├── app.py               # инициализация Flask и ID.db
├── routes.py            # обработчик постбэков
└── req.txt              # зависимости сервиса
установка.txt            # подробная инструкция по деплою
```

## Настройка

Заполните `bot/config.py`:

| Параметр | Описание |
|---|---|
| `BOT_TOKEN` | Токен бота от [@BotFather](https://t.me/BotFather) |
| `CHANNEL_URL` | Ссылка на канал для обязательной подписки |
| `CHANNEL_ID` | ID канала (можно узнать через [@getmyid_bot](https://t.me/getmyid_bot)); бот должен быть админом канала |
| `SUPP` | Ссылка на аккаунт поддержки |
| `ADMIN_ID` | Ваш Telegram ID |
| `DB_PATH` | Путь к базе постбэков, по умолчанию `/root/flask/ID.db` |

Реферальная ссылка и промокод меняются через `/admin`, их не нужно задавать в конфиге.

> ⚠️ Не публикуйте настоящий `BOT_TOKEN` в открытом репозитории. Лучше читать его из переменной окружения или `.env`, а `config.py` добавить в `.gitignore`.

## Установка на сервер (Ubuntu)

Пошаговая инструкция с примерами есть в [`установка.txt`](установка.txt). Кратко:

### 1. Бот

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3.12-venv -y   # версия venv должна совпадать с версией Python

# скопируйте папку bot в /root/bot
cd /root/bot
python3 -m venv venv
source venv/bin/activate
pip install -r req.txt
```

`/lib/systemd/system/bot.service`:

```ini
[Unit]
Description=bot
After=network.target

[Service]
Type=idle
Restart=always
RestartSec=3
User=root
WorkingDirectory=/root/bot/
ExecStart=/bin/bash -c 'source /root/bot/venv/bin/activate && exec python3 main.py'

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bot.service
```

### 2. Сервис постбэков

```bash
# скопируйте папку flask в /root/flask
cd /root/flask
python3 -m venv venv
source venv/bin/activate
pip install -r req.txt
```

`/lib/systemd/system/flask.service`:

```ini
[Unit]
Description=Flask Application
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/root/flask
Environment='PATH=/root/flask/venv/bin'
ExecStart=/root/flask/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:8000 app:app

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now flask.service
```

### 3. Постбэки в кабинете Pocket Option

В разделе **Постбэк 2.0** добавьте два постбэка (тип Global или для конкретной ссылки), URL для обоих: `http://<IP_сервера>:8000`.

| Событие | Параметры |
|---|---|
| Регистрация | `trader_id` |
| Первый депозит | `trader_id`, `sumdep` |

Ссылку из поля «Превью» (вида `https://u3.shortink.io/smart/XXXXXX?trader_id={}`) установите в бота как реферальную через `/admin` → «Смена реф ссылки».

## Проверка

- Бот отвечает на `/start`.
- `curl "http://<IP>:8000/?trader_id=123"` возвращает JSON о добавлении ID.
- Логи: `journalctl -u bot -f` и `journalctl -u flask -f`.

## Запуск локально

```bash
# терминал 1
cd flask && pip install -r req.txt && python app.py

# терминал 2 (в config.py укажите DB_PATH на ../flask/ID.db)
cd bot && pip install -r req.txt && python main.py
```
