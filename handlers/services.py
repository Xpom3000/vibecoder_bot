"""Сценарий 3 (паспорт бота): раздел услуг."""
from aiogram import F, Router
from aiogram.types import CallbackQuery

from data.portfolio import SERVICES
from keyboards.inline import service_card_kb, service_list_kb

router = Router()

LIST_TEXT = "Что делаем: выбери направление, расскажу подробнее 👇"


def _find_service(slug: str) -> dict | None:
    return next((s for s in SERVICES if s["slug"] == slug), None)


def _render_card(service: dict) -> str:
    return (
        f"<b>{service['title']}</b>\n\n"
        f"{service['description']}\n\n"
        f"💰 Цена: {service['price']}\n"
        f"⏱ Срок: {service['duration']}"
    )


@router.callback_query(F.data == "menu:services")
async def show_service_list(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(LIST_TEXT, reply_markup=service_list_kb(SERVICES))


@router.callback_query(F.data == "services:list")
async def back_to_list(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(LIST_TEXT, reply_markup=service_list_kb(SERVICES))


@router.callback_query(F.data.startswith("services:card:"))
async def show_service_card(callback: CallbackQuery) -> None:
    slug = callback.data.split(":")[-1]
    service = _find_service(slug)

    await callback.answer()

    if service is None:
        await callback.message.answer("Такая услуга не нашлась 🤔")
        return

    await callback.message.edit_text(_render_card(service), reply_markup=service_card_kb())
