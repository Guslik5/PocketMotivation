from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import CHANNEL_URL, SUPP
from database.db import DataBase
from other.languages import languages


class ClientKeyboard:

    @staticmethod
    async def start_keyboard(lang: str):
        ikb = InlineKeyboardBuilder()
        ikb.button(text=languages[lang]["subscribe"], url=CHANNEL_URL)
        ikb.button(text=languages[lang]["check"], callback_data="check")
        ikb.adjust(1)
        return ikb.as_markup()

    @staticmethod
    async def languages_board(data: str):
        ikb = InlineKeyboardBuilder()
        ikb.button(text="🇷🇺 Русский", callback_data=f"{data}|ru")
        ikb.button(text="🇬🇧 English", callback_data=f"{data}|en")
        ikb.button(text="🇺🇿 O'zbek", callback_data=f"{data}|uz")
        ikb.adjust(2)
        return ikb.as_markup()

    @staticmethod
    async def menu_keyboard(user_info: list, lang: str):
        ikb = InlineKeyboardBuilder()

        ikb.button(text=languages[lang]["instruction"], callback_data="instruction")
        ikb.button(text=languages[lang]["support"], url=SUPP)
        ikb.button(text=languages[lang]["choose_lang"], callback_data="get_lang")

        if user_info[0] != "verifed":
            ikb.button(text=languages[lang]["get_signal"], callback_data="register")
        elif user_info[0] == "verifed" and user_info[3] != "dep":
            ikb.button(text=languages[lang]["get_signal"], callback_data="wait_depozit")
        elif user_info[0] == "verifed" and user_info[3] == "dep":
            ikb.button(text=languages[lang]["get_signal"],
                       web_app=types.WebAppInfo(url="https://th3rrry.github.io/trading/"))

        ikb.adjust(1, 2, 1)

        return ikb.as_markup()

    @staticmethod
    async def register_keyboard(callback: types.CallbackQuery, lang: str):
        ikb = InlineKeyboardBuilder()
        new_ref_url = f"{(await DataBase.get_ref())}"
        ikb.button(text=languages[lang]["register_action"], url=new_ref_url)
        ikb.button(text=languages[lang]["back"], callback_data="back")
        ikb.adjust(1)
        return ikb.as_markup()

    @staticmethod
    async def dep_keyboard(user_id, lang: str):
        ikb = InlineKeyboardBuilder()
        new_ref_url = f"{(await DataBase.get_ref())}"
        ikb.button(text=languages[lang]["dep"], url=new_ref_url)
        ikb.button(text=languages[lang]["check_dep"], callback_data="search_deposit")
        ikb.button(text=languages[lang]["back"], callback_data="back")
        ikb.adjust(1)
        return ikb.as_markup()

    @staticmethod
    async def back_keyboard(lang: str):
        ikb = InlineKeyboardBuilder()
        ikb.button(text=languages[lang]["back"], callback_data="back")
        return ikb.as_markup()

    @staticmethod
    async def signal_keyboard(user_info: list, lang: str):
        if user_info[0] == "verifed" and user_info[3] == "dep":
            ikb = InlineKeyboardBuilder()
            ikb.button(text=languages[lang]["get_signal"],
                       web_app=types.WebAppInfo(url="https://th3rrry.github.io/trading/"))
            ikb.button(text=languages[lang]["back"], callback_data="back")
            ikb.adjust(1)
            return ikb.as_markup()
        else:
            return None
