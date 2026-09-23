"""Тесты правила оплаты: статус заказа становится «оплачен» только через
подтверждённый платёж (can_confirm_payment), а не откуда угодно.

Реальные запросы к СБП/Telegram здесь не нужны — эти тесты проверяют
чистую бизнес-логику (services/cart.py). Хендлер-уровень с реальным
Telegram Bot API замокан отдельно в test_payment_handlers.py.
"""
from services.cart import (
    add_item,
    can_confirm_payment,
    create_order,
    get_cart,
    get_order,
    set_order_status,
)

USER = 1


# --- can_confirm_payment(): чистая функция, без БД ---

def test_cannot_confirm_order_awaiting_payment():
    """Клиент ещё не нажимал «Я оплатил(а)» — подтверждать нечего."""
    order = {"status": "ожидает оплаты"}
    assert can_confirm_payment(order) is False


def test_can_confirm_order_under_review():
    """Клиент отметил оплату, заказ «на проверке» — можно подтвердить."""
    order = {"status": "на проверке"}
    assert can_confirm_payment(order) is True


def test_cannot_confirm_already_paid_order():
    """Граничный случай: повторное подтверждение уже оплаченного заказа."""
    order = {"status": "оплачен"}
    assert can_confirm_payment(order) is False


def test_cannot_confirm_missing_order():
    assert can_confirm_payment(None) is False


# --- Полный жизненный цикл статуса на реальной (тестовой) БД ---

async def test_status_becomes_paid_only_through_confirmed_flow(fresh_db):
    await add_item(USER, "promo")
    lines = await get_cart(USER)
    order_id = await create_order(USER, lines)

    # 1. Сразу после оформления заказ ждёт оплаты — подтверждать ещё нельзя.
    order = await get_order(order_id)
    assert order["status"] == "ожидает оплаты"
    assert can_confirm_payment(order) is False

    # 2. Клиент нажимает «Я оплатил(а)» -> статус "на проверке".
    await set_order_status(order_id, "на проверке")
    order = await get_order(order_id)
    assert can_confirm_payment(order) is True

    # 3. Только теперь владелец может подтвердить -> "оплачен".
    await set_order_status(order_id, "оплачен")
    order = await get_order(order_id)
    assert order["status"] == "оплачен"

    # 4. Повторное подтверждение больше недоступно.
    assert can_confirm_payment(order) is False


async def test_status_never_jumps_straight_to_paid_without_review(fresh_db):
    """Нельзя подтвердить оплату заказа, который клиент ещё не помечал
    оплаченным (минуя «на проверке»)."""
    await add_item(USER, "landing")
    lines = await get_cart(USER)
    order_id = await create_order(USER, lines)

    order = await get_order(order_id)
    assert order["status"] == "ожидает оплаты"
    assert can_confirm_payment(order) is False  # именно поэтому хендлер не даст подтвердить
