import asyncio
from aiogram import F, Router, types, Bot
from keyboards.admin import admin_command
from keyboards.admin import cancel_adm
from aiogram.fsm.context import FSMContext
from database.db import DataBase
from config import ADMIN_ID
from other.languages import languages
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter


class AdminStates(StatesGroup):
    mailing_text = State()


class ChangeRef(StatesGroup):
    enter_ref = State()


class ChangePromo(StatesGroup):
    enter_promo = State()


router = Router()


@router.message(F.text == '/admin')
async def admin_handler(message: types.Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.clear()
        await message.answer("<b>Админ панель 🥷</b>",
                             reply_markup=await admin_command(), parse_mode="HTML")


@router.callback_query(F.data == 'stat')
async def statistics_handler(callback: types.CallbackQuery):
    users_count = await DataBase.get_users_count()
    verif_count = await DataBase.get_verified_users_count()
    dep_count = await DataBase.get_dep_users_count()
    
    statistics_message = (
        f"<b>Статистика бота:</b>\n\n"
        f"<b>Общее количество пользователей:</b> <code>{users_count}</code>\n"
        f"<b>Количество пользователей прошедших верификацию:</b> <code>{verif_count}</code>\n"
        f"<b>Количество пользователей с первым депозитом:</b> <code>{dep_count}</code>"
    )
    await callback.message.answer(statistics_message, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == 'mailing')
async def mailing_state(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте сообщение")
    await state.set_state(AdminStates.mailing_text)


@router.message(AdminStates.mailing_text)
async def mailing_state(message: types.Message, state: FSMContext, bot: Bot):
    mailing_message = message.message_id
    ikb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text='Отправить', callback_data='send_mailing'), types.InlineKeyboardButton(
            text='Отмена', callback_data='decline_mailing')]
    ])
    await bot.copy_message(chat_id=message.chat.id, from_chat_id=message.chat.id,
                           message_id=mailing_message, reply_markup=ikb, parse_mode="HTML")

    await state.update_data(msg=mailing_message)


@router.callback_query(F.data == 'send_mailing')
async def mailing_handler(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    errors_count = 0
    good_count = 0
    data = await state.get_data()
    mailing_message = data['msg']
    users = await DataBase.get_users()
    await callback.message.delete()
    await callback.message.answer("Рассылка начата...")
    for i in users:
        try:
            await bot.copy_message(chat_id=i[1], from_chat_id=callback.from_user.id,
                                   message_id=mailing_message, parse_mode="HTML")
            good_count += 1
        except Exception as ex:
            errors_count += 1
            print(ex)

    await callback.message.answer(f"<b>Кол-во отосланных сообщений:</b> <code>{good_count}</code>\n\
<b>Кол-во пользователей заблокировавших бота:</b> <code>{errors_count}</code>", parse_mode="HTML")
    await callback.answer()
    await state.clear()


@router.callback_query(F.data == 'decline_mailing')
async def decline_mailing(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Рассылка отменена", reply_markup=await admin_command())
    await state.clear()


@router.callback_query(F.data == "change_ref")
async def change_referral_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    lang = await DataBase.get_lang(callback.from_user.id)
    await asyncio.sleep(0.5)
    await callback.message.answer(languages[lang]["enter_new_ref"])
    await state.set_state(ChangeRef.enter_ref)


@router.message(ChangeRef.enter_ref)
async def change_ref_message_state(message: types.Message, state: FSMContext):
    lang = await DataBase.get_lang(message.from_user.id)
    await message.answer(languages[lang]["ref_changed"])
    await DataBase.edit_ref(message.text)
    await state.clear()


@router.callback_query(F.data == "change_promo")
async def change_promo_callback_handler(callback: types.CallbackQuery, state: FSMContext):
    lang = await DataBase.get_lang(callback.from_user.id)
    await asyncio.sleep(0.5)
    await callback.message.answer(languages[lang]["enter_new_promo"])
    await state.set_state(ChangePromo.enter_promo)


@router.message(ChangePromo.enter_promo)
async def change_promo_message_state(message: types.Message, state: FSMContext):
    lang = await DataBase.get_lang(message.from_user.id)
    await message.answer(languages[lang]["promo_changed"])
    await DataBase.edit_promo(message.text)
    await state.clear()


@router.callback_query(F.data == 'cancel')
async def cancel_action(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("<b>Действие отменено.</b>", parse_mode="HTML")
