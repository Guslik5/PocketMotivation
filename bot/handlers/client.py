import asyncio
import sqlite3
import datetime
from config import DB_PATH, CHANNEL_ID, ADMIN_ID
from aiogram import F, Router, types, Bot
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from database.db import DataBase
from keyboards.client import ClientKeyboard
from other.filters import ChatJoinFilter
from other.languages import languages
from aiogram.types import FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import StateFilter

router = Router()
last_message_ids = {}
error_messages_ids = {}
language_selected = False


class Form(StatesGroup):
    waiting_for_id = State()


@router.message(CommandStart())
async def start_command(message: types.Message, user_id: int = 0, state: FSMContext = None):
    global language_selected

    user_id = message.from_user.id if user_id == 0 else user_id

    if not language_selected:
        if user_id != ADMIN_ID:
            username = message.from_user.username or "Не указано"
            full_name = message.from_user.full_name or "Не указано"
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            admin_message = (
                f"<b>✔Событие: нажатие /start.</b>\n\n"
                f"<b>Username: {username}</b>\n"
                f"<b>ID: {user_id}</b>\n"
                f"<b>Имя: {full_name}</b>\n"
                f"<b>Время: {current_time}</b>"
            )

            try:
                await message.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode='html')
            except Exception as e:
                print(f"[!] Не удалось отправить сообщение админу: {e}")

    user = await DataBase.get_user_info(user_id)

    if user is None:
        await get_language(message, True)
        return

    language_selected = False

    if state is not None:
        current_state = await state.get_state()
        if current_state is not None:
            await state.clear()

    await delete_previous_error_messages(message.bot, user_id)

    chat_member = await message.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)

    lang = await DataBase.get_lang(user_id)

    if chat_member.status in ["member", "creator", "administrator"]:
        caption = languages[lang]["welcome_message"]
        photo_path = 'image/main.png'
        reply_markup = await ClientKeyboard.menu_keyboard(user, lang)

        photo = FSInputFile(photo_path)
        if user_id in last_message_ids and last_message_ids[user_id] is not None:
            try:
                await asyncio.sleep(0.2)
                await message.bot.delete_message(chat_id=user_id, message_id=last_message_ids[user_id])
            except Exception as e:
                print(f"Ошибка удаления старого сообщения: {e}")

        new_message = await message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        caption = languages[lang]["welcome"]
        reply_markup = await ClientKeyboard.start_keyboard(lang)

        new_message = await message.answer(
            text=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    last_message_ids[user_id] = new_message.message_id


@router.callback_query(F.data.startswith("sel_lang"))
async def select_language(callback: CallbackQuery):
    global language_selected
    data = callback.data.split("|")
    await asyncio.sleep(0.2)
    await callback.message.delete()

    username = callback.from_user.username if callback.from_user.username else "user"

    await DataBase.register(callback.from_user.id, data[2], username)
    language_selected = True
    await start_command(message=callback.message, user_id=callback.from_user.id)


@router.callback_query(F.data.startswith("resel_lang"))
async def resel_language(callback: CallbackQuery):
    global language_selected
    data = callback.data.split("|")
    await asyncio.sleep(0.2)
    await callback.message.delete()
    await DataBase.update_lang(int(data[1]), data[2])
    language_selected = True
    await start_command(message=callback.message, user_id=int(data[1]))


@router.callback_query(F.data == "get_lang")
async def get_language(query: Message | CallbackQuery, first: bool = False):
    if isinstance(query, CallbackQuery):
        message = query.message
        user_id = query.from_user.id
    else:
        message = query
        user_id = message.from_user.id

    if user_id == message.bot.id:
        print(f"Ошибка: {str(e)}")
        return

    try:
        pass
    except Exception as e:
        print(f"Ошибка: {str(e)}")

    if first:
        prefix = f"sel_lang|{user_id}"
    else:
        prefix = f"resel_lang|{user_id}"

    photo_path = 'image/language.png'
    photo = FSInputFile(photo_path)

    if user_id in last_message_ids and last_message_ids[user_id] is not None:
        try:
            await asyncio.sleep(0.2)
            await message.bot.delete_message(chat_id=user_id,
                                             message_id=last_message_ids[user_id])
        except Exception as e:
            print(f"Ошибка: {str(e)}")

    new_message = await message.bot.send_photo(
        chat_id=user_id,
        photo=photo,
        caption="<b>Добро пожаловать в бот👋🏼</b>\n\nВыберите язык / Choose a language / Tilni tanlang:",
        parse_mode="HTML",
        reply_markup=await ClientKeyboard.languages_board(prefix)
    )
    last_message_ids[user_id] = new_message.message_id


@router.callback_query(F.data.in_(["back", "check"]), ChatJoinFilter())
async def menu_output(callback: types.CallbackQuery, state: FSMContext):
    await asyncio.sleep(0.2)
    await callback.message.delete()
    await delete_previous_error_messages(callback.bot, callback.message.chat.id)

    if state is not None:
        current_state = await state.get_state()
        if current_state is not None:
            await state.clear()

    user_info = await DataBase.get_user_info(callback.from_user.id)
    lang = await DataBase.get_lang(callback.from_user.id)
    new_ref_url = f"{(await DataBase.get_ref())}"
    promo = f"{(await DataBase.get_promo())}"

    languages[lang]["register_info"].format(ref_url=new_ref_url, promo=promo)

    photo = types.FSInputFile("image/main.png")

    new_message = await callback.message.answer_photo(
        photo,
        caption=languages[lang]["welcome_message"],
        parse_mode="HTML",
        reply_markup=await ClientKeyboard.menu_keyboard(user_info, lang)
    )
    last_message_ids[callback.from_user.id] = new_message.message_id


@router.callback_query(F.data == "register")
async def register_handler(callback: types.CallbackQuery, state: FSMContext):
    lang = await DataBase.get_lang(callback.from_user.id)

    user_status = await DataBase.get_user(callback.from_user.id)
    new_ref_url = f"{(await DataBase.get_ref())}"
    promo = f"{(await DataBase.get_promo())}"

    if user_status and user_status['verifed']:
        await state.clear()

    text = languages[lang]["register_info"].format(ref_url=new_ref_url, promo=promo)

    if callback.message:
        try:
            await asyncio.sleep(0.2)
            await callback.message.delete()
        except Exception as e:
            print(f"Ошибка: {str(e)}")

    photo = types.FSInputFile("image/registration.png")

    new_message = await callback.message.answer_photo(
        photo=photo,
        caption=text,
        parse_mode="HTML",
        reply_markup=await ClientKeyboard.register_keyboard(callback, lang)
    )
    last_message_ids[callback.from_user.id] = new_message.message_id

    await state.set_state(Form.waiting_for_id)


@router.message(StateFilter(Form.waiting_for_id))
async def process_id_input(message: types.Message, state: FSMContext):
    user_id_str = message.text.strip()

    if user_id_str.isdigit():
        input_user_id = int(user_id_str)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM id WHERE id = ?", (input_user_id,))
        user_info = cursor.fetchone()

        conn.close()

        if user_info is None:
            await send_account_not_found_message(message)
            return

        try:
            await wait_deposit(message, message.from_user.id)
            sender_user_id = message.from_user.id
            await DataBase.update_verifed(sender_user_id)
            await DataBase.add_trader_id(sender_user_id, input_user_id)

            if sender_user_id != ADMIN_ID:
                username = message.from_user.username or "Не указано"
                full_name = message.from_user.full_name or "Не указано"
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                admin_message = (
                    f"<b>✔️ Событие: регистрация.</b>\n\n"
                    f"<b>Username: {username}</b>\n"
                    f"<b>ID: {sender_user_id}</b>\n"
                    f"<b>Trader ID: {input_user_id}</b>\n"
                    f"<b>Имя: {full_name}</b>\n"
                    f"<b>Время: {current_time}</b>"
                )

                try:
                    await message.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode='html')
                except Exception as e:
                    print(f"[!] Не удалось отправить сообщение админу: {e}")

        except Exception as e:
            print(f"Ошибка: {str(e)}")
        finally:
            await state.clear()

    else:
        await handle_invalid_format(message)


async def handle_invalid_format(message: types.Message):
    await delete_previous_error_messages(message.bot, message.chat.id)
    text = languages[await DataBase.get_lang(message.from_user.id)]["invalid_format"]
    error_message = await message.answer(text)
    error_messages_ids[message.chat.id] = error_message.message_id


async def send_account_not_found_message(message: types.Message):
    await delete_previous_error_messages(message.bot, message.chat.id)
    text = languages[await DataBase.get_lang(message.from_user.id)]["error_id"]
    error_message = await message.answer(text)
    error_messages_ids[message.chat.id] = error_message.message_id


async def delete_previous_error_messages(bot: Bot, chat_id: int):
    if chat_id in error_messages_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=error_messages_ids[chat_id])
            del error_messages_ids[chat_id]
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")


async def wait_deposit(message: types.Message, input_user_id: int):
    await delete_previous_error_messages(message.bot, message.chat.id)

    if input_user_id in last_message_ids and last_message_ids[input_user_id] is not None:
        try:
            await asyncio.sleep(0.2)
            await message.bot.delete_message(chat_id=message.chat.id,
                                             message_id=last_message_ids[input_user_id])
            del last_message_ids[input_user_id]
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {str(e)}")

    new_ref_url = f"{(await DataBase.get_ref())}"
    lang = await DataBase.get_lang(message.from_user.id)
    text = languages[lang]["wait_depozit"].format(ref_url=new_ref_url)

    await asyncio.sleep(0.7)

    photo = types.FSInputFile("image/dep.png")
    new_message = await message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=await ClientKeyboard.dep_keyboard(input_user_id, lang),
        parse_mode="HTML"
    )
    last_message_ids[input_user_id] = new_message.message_id


@router.callback_query(F.data == "search_deposit")
async def search_deposit_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = await DataBase.get_lang(user_id)
    trader_id = await DataBase.get_trader_id(user_id)

    if trader_id is None:
        return

    conn = sqlite3.connect(DB_PATH)
    print(f"Используемый путь к базе данных: {DB_PATH}")
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT deposit FROM ID WHERE id = ?", (trader_id,))
        deposit_row = cursor.fetchone()

        if deposit_row is None:
            return

        deposit_status = deposit_row[0]
        photo = types.FSInputFile("image/signal.png")

        if deposit_status:
            await DataBase.update_deposit_status(user_id)
            await callback.message.delete()
            user_info = await DataBase.get_user_info(user_id)
            new_message = await callback.bot.send_photo(
                chat_id=user_id,
                photo=photo,
                caption=languages[lang]["depozit_success"],
                parse_mode="HTML",
                reply_markup=await ClientKeyboard.signal_keyboard(user_info, lang)
            )
            last_message_ids[user_id] = new_message.message_id

            if user_id != ADMIN_ID:
                username = callback.from_user.username or "Не указано"
                full_name = callback.from_user.full_name or "Не указано"
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                admin_message = (
                    f"<b>✔️ Событие: подтвержденный депозит!</b>\n\n"
                    f"<b>Username: {username}</b>\n"
                    f"<b>ID: {user_id}</b>\n"
                    f"<b>Trader ID: {trader_id}</b>\n"
                    f"<b>Имя: {full_name}</b>\n"
                    f"<b>Время: {current_time}</b>"
                )

                try:
                    await callback.bot.send_message(chat_id=ADMIN_ID, text=admin_message, parse_mode='html')
                except Exception as e:
                    print(f"[!] Не удалось отправить сообщение админу: {e}")

        else:
            text = languages[lang]["no_dep"]
            await callback.answer(text)

    except sqlite3.OperationalError as e:
        print(f"Ошибка при работе с БД: {e}")
        await callback.answer("Произошла ошибка при обращении к базе данных.")

    finally:
        conn.close()


@router.callback_query(F.data == "instruction")
async def instruction_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    new_ref_url = f"{(await DataBase.get_ref())}"
    promo = f"{(await DataBase.get_promo())}"
    lang = await DataBase.get_lang(callback.from_user.id)
    text = languages[lang]["instruction_info"].format(ref_url=new_ref_url, promo=promo)

    await asyncio.sleep(0.2)
    await callback.message.delete()

    photo = types.FSInputFile("image/instru.png")

    new_message = await callback.message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=await ClientKeyboard.back_keyboard(lang),
        parse_mode="HTML"
    )
    last_message_ids[user_id] = new_message.message_id


@router.callback_query(F.data == "wait_depozit")
async def dep_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    new_ref_url = f"{(await DataBase.get_ref())}"
    lang = await DataBase.get_lang(callback.from_user.id)
    text = languages[lang]["wait_depozit"].format(ref_url=new_ref_url)

    await asyncio.sleep(0.2)
    await callback.message.delete()

    photo = types.FSInputFile("image/dep.png")

    new_message = await callback.message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=await ClientKeyboard.dep_keyboard(user_id, lang),
        parse_mode="HTML"
    )
    last_message_ids[user_id] = new_message.message_id
