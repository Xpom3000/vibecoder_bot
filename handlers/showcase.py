"""Витрина услуг: карточки товара (название, описание, цена) с кнопкой
«Добавить в корзину» под каждой.

Отдельная фича от раздела «Услуги» (handlers/services.py, инлайн-меню).
Данные берутся из того же SERVICES в data/portfolio.py, которым уже
пользуются раздел «Услуги» и база знаний DeepSeek — один источник данных.

Просмотр и оформление самой корзины — в handlers/cart.py. Здесь только
добавление позиций (сюда естественно ведёт кнопка на карточке товара).

Вызывается постоянной кнопкой меню (keyboards/reply.py), поэтому это
message-хендлер на точный текст кнопки, а не callback_query — и он обязан
быть подключён в bot.py раньше handlers/faq.py.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from data.portfolio import SERVICES
from keyboards.inline import add_to_cart_kb
from keyboards.reply import BTN_SHOWCASE
from services.cart import add_item

router = Router()

_SERVICES_BY_SLUG = {s["slug"]: s for s in SERVICES}


def _render_card(service: dict) -> str:
    return f"<b>{service['title']}</b>\n{service['description']}\n\n💰 {service['price']}"


@router.message(F.text == BTN_SHOWCASE)
async def show_showcase(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Вот что я делаю 👇")
    for service in SERVICES:
        await message.answer(_render_card(service), reply_markup=add_to_cart_kb(service["slug"]))


@router.callback_query(F.data.startswith("cart:add:"))
async def add_to_cart(callback: CallbackQuery) -> None:
    slug = callback.data.split(":", 2)[-1]
    service = _SERVICES_BY_SLUG.get(slug)

    await callback.answer()

    if service is None:
        # Услугу успели убрать из каталога, пока пользователь смотрел витрину.
        await callback.message.answer("Эта услуга больше не найдена — попробуй открыть витрину заново.")
        return

    quantity = await add_item(callback.from_user.id, slug)

    if quantity > 1:
        note = f"«{service['title']}» — теперь в корзине: {quantity} шт."
    else:
        note = f"«{service['title']}» добавлен(а) в корзину."

    await callback.message.answer(f"✅ {note}\nПосмотреть корзину — кнопка «🛒 Корзина» в меню.")
