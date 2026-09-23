"""Тесты оформления заказа (services/cart.py): создание заказа из корзины,
очистка корзины после оформления, попытка оформления при пустой корзине.
"""
from services.cart import add_item, can_checkout, create_order, get_cart, get_order

USER = 1


async def test_checkout_creates_order_with_correct_data(fresh_db):
    await add_item(USER, "landing")
    await add_item(USER, "promo")

    lines = await get_cart(USER)
    order_id = await create_order(USER, lines)

    order = await get_order(order_id)
    assert order is not None
    assert order["telegram_user_id"] == USER
    assert order["status"] == "ожидает оплаты"
    assert order["total_text"] == "25 000 ₽"


async def test_checkout_clears_the_cart(fresh_db):
    await add_item(USER, "landing")

    lines = await get_cart(USER)
    await create_order(USER, lines)

    cart_after = await get_cart(USER)
    assert cart_after == []


async def test_checkout_does_not_affect_other_users_cart(fresh_db):
    await add_item(USER, "landing")
    await add_item(2, "promo")

    lines = await get_cart(USER)
    await create_order(USER, lines)

    other_user_cart = await get_cart(2)
    assert len(other_user_cart) == 1  # корзина другого пользователя не тронута


async def test_cannot_checkout_empty_cart(fresh_db):
    """Граничный случай: попытка оформить заказ с пустой корзиной.

    can_checkout() — то самое правило, которое handlers/cart.py проверяет
    перед вызовом create_order(); здесь оно тестируется напрямую.
    """
    empty_cart = await get_cart(USER)  # пользователь ничего не добавлял
    assert empty_cart == []
    assert can_checkout(empty_cart) is False


async def test_can_checkout_non_empty_cart(fresh_db):
    await add_item(USER, "landing")
    cart = await get_cart(USER)
    assert can_checkout(cart) is True


async def test_order_snapshot_survives_catalog_changes(fresh_db, monkeypatch):
    """Заказ хранит снимок (items_json/total_text) на момент оформления —
    даже если каталог после этого поменяется, история заказа не съезжает."""
    await add_item(USER, "landing")
    lines = await get_cart(USER)
    order_id = await create_order(USER, lines)

    order_before = await get_order(order_id)
    assert order_before["total_text"] == "15 000 ₽"

    # "Меняем прайс" в каталоге задним числом — заказ не должен пересчитаться.
    import services.cart as cart_module

    monkeypatch.setitem(cart_module._SERVICES_BY_SLUG["landing"], "price", "999 999 ₽")

    order_after = await get_order(order_id)
    assert order_after["total_text"] == "15 000 ₽"  # снимок не изменился
