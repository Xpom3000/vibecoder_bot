"""Витрина услуг + заглушка корзины.

Отдельная фича от раздела «Услуги» (handlers/services.py, инлайн-меню):
здесь все услуги показываются сразу как карточки товара — название,
короткое описание, цена — с кнопкой «Добавить в корзину» под каждой.
Данные берутся из того же SERVICES в data/portfolio.py, которым уже
пользуются и раздел «Услуги», и база знаний DeepSeek — один источник данных.

Вызывается постоянной кнопкой меню (keyboards/reply.py), поэтому это
message-хендлеры на точный текст кнопки, а не callback_query — и они
обязаны быть подключены в bot.py раньше handlers/faq.py.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from data.portfolio import SERVICES
from keyboards.inline import add_to_cart_kb
from keyboards.reply import BTN_CART, BTN_SHOWCASE

router = Router()

CART_STUB_TEXT = (
    "🛒 Корзина пока в разработке — скоро здесь можно будет собрать заказ "
    "из нескольких услуг и оформить его."
)


def _render_card(service: dict) -> str:
    return f"<b>{service['title']}</b>\n{service['description']}\n\n💰 {service['price']}"


@router.message(F.text == BTN_SHOWCASE)
async def show_showcase(message: Message) -> None:
    await message.answer("Вот что я делаю 👇")
    for service in SERVICES:
        await message.answer(_render_card(service), reply_markup=add_to_cart_kb(service["slug"]))


@router.message(F.text == BTN_CART)
async def show_cart_stub(message: Message) -> None:
    await message.answer(CART_STUB_TEXT)


@router.callback_query(F.data.startswith("cart:add:"))
async def add_to_cart_stub(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(CART_STUB_TEXT)
