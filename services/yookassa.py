"""Клиент ЮKassa (REST API v3) для онлайн-оплаты заказов.

Используется только когда сумма заказа полностью определена числом — нет
позиций "от N ₽" или "обсуждается индивидуально" (см.
services.cart.get_exact_total()). Для остальных заказов работает прежняя
ручная схема оплаты по СБП (data.portfolio.PAYMENT, handlers/payment.py).

Статус оплаты проверяется явным запросом к ЮKassa (get_payment_status), а
не через редирект пользователя — так бот сам убеждается в оплате, а не
верит ни клиенту, ни редиректу браузера.
"""
import logging
import uuid

import aiohttp

from config import YOOKASSA_SECRET_KEY, YOOKASSA_SHOP_ID

API_URL = "https://api.yookassa.ru/v3/payments"
REQUEST_TIMEOUT = 20

# Статус в терминах ЮKassa, который означает "деньги реально получены".
# waiting_for_capture — здесь не считаем оплаченным: это означает, что
# платёж захолдирован, но ещё не списан (у нас capture=True, так что этот
# статус почти не должен встречаться, но на всякий случай не доверяем ему).
CONFIRMED_STATUS = "succeeded"

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY)


def is_payment_confirmed(status: str | None) -> bool:
    """Чистая функция: True только для статуса, который ЮKassa считает
    подтверждённой оплатой. Вынесена отдельно, чтобы бизнес-правило
    "оплачен только при succeeded" можно было протестировать без HTTP."""
    return status == CONFIRMED_STATUS


async def create_payment(amount_rub: int, description: str, return_url: str) -> dict | None:
    """Создаёт платёж в ЮKassa.

    Возвращает {"id": str, "confirmation_url": str} или None при ошибке
    (нет конфигурации, сетевая ошибка, неожиданный ответ) — вызывающий код
    должен в этом случае откатиться на ручную схему оплаты.
    """
    if not is_configured():
        logger.warning("ЮKassa не настроена (нет shopId/secretKey) — онлайн-оплата недоступна.")
        return None

    payload = {
        "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": return_url},
        "capture": True,
        "description": description,
    }
    headers = {"Idempotence-Key": str(uuid.uuid4())}
    auth = aiohttp.BasicAuth(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)

    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout, auth=auth) as session:
            async with session.post(API_URL, json=payload, headers=headers) as resp:
                if resp.status not in (200, 201):
                    body = await resp.text()
                    logger.error("Ошибка создания платежа ЮKassa %s: %s", resp.status, body)
                    return None
                data = await resp.json()
    except Exception:
        logger.exception("Не удалось создать платёж в ЮKassa")
        return None

    try:
        return {"id": data["id"], "confirmation_url": data["confirmation"]["confirmation_url"]}
    except (KeyError, TypeError):
        logger.error("Неожиданный формат ответа ЮKassa при создании платежа: %s", data)
        return None


async def get_payment_status(payment_id: str) -> str | None:
    """Текущий статус платежа в ЮKassa ("pending" | "waiting_for_capture" |
    "succeeded" | "canceled") или None при ошибке запроса."""
    if not is_configured():
        return None

    auth = aiohttp.BasicAuth(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
    url = f"{API_URL}/{payment_id}"

    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout, auth=auth) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("Ошибка проверки статуса платежа ЮKassa %s: %s", resp.status, body)
                    return None
                data = await resp.json()
    except Exception:
        logger.exception("Не удалось проверить статус платежа в ЮKassa")
        return None

    return data.get("status")
