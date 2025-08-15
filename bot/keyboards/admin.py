from aiogram.utils.keyboard import InlineKeyboardBuilder


async def admin_command():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Рассылка", callback_data="mailing")
    ikb.button(text="Статистика", callback_data="stat")
    ikb.button(text="Смена реф ссылки", callback_data="change_ref")
    ikb.button(text="Смена промокода", callback_data="change_promo")
    ikb.adjust(2, 2)
    return ikb.as_markup()


async def cancel_adm():
    ikb = InlineKeyboardBuilder()
    ikb.button(text="Отмена", callback_data="cancel")
    ikb.adjust(1)
    return ikb.as_markup()
