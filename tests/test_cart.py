"""Тесты корзины (services/cart.py): добавление, удаление, подсчёт суммы,
повторное добавление одной услуги, удаление из пустой корзины.
"""
from services.cart import add_item, format_total, get_cart, remove_item

USER = 1


async def test_new_cart_is_empty(fresh_db):
    cart = await get_cart(USER)
    assert cart == []


async def test_add_item(fresh_db):
    quantity = await add_item(USER, "landing")

    assert quantity == 1
    cart = await get_cart(USER)
    assert len(cart) == 1
    assert cart[0].slug == "landing"
    assert cart[0].quantity == 1


async def test_add_same_service_twice_increments_quantity_not_duplicates_row(fresh_db):
    """Граничный случай: одна и та же услуга добавлена в корзину дважды —
    должно стать количество 2 в одной строке, а не два отдельных товара."""
    await add_item(USER, "landing")
    quantity = await add_item(USER, "landing")

    assert quantity == 2
    cart = await get_cart(USER)
    assert len(cart) == 1  # одна позиция, не дублируется
    assert cart[0].quantity == 2


async def test_remove_item(fresh_db):
    await add_item(USER, "landing")

    removed = await remove_item(USER, "landing")

    assert removed is True
    cart = await get_cart(USER)
    assert cart == []


async def test_remove_from_empty_cart_returns_false_without_crashing(fresh_db):
    """Граничный случай: удаление из пустой корзины (или повторное «Убрать»
    по уже удалённой позиции) не должно падать — просто False."""
    removed = await remove_item(USER, "landing")
    assert removed is False


async def test_remove_twice_second_time_returns_false(fresh_db):
    """Граничный случай: «Убрать» дважды по одной и той же позиции."""
    await add_item(USER, "landing")

    first = await remove_item(USER, "landing")
    second = await remove_item(USER, "landing")

    assert first is True
    assert second is False


async def test_removing_one_item_does_not_affect_others(fresh_db):
    await add_item(USER, "landing")
    await add_item(USER, "promo")

    await remove_item(USER, "landing")

    cart = await get_cart(USER)
    assert [line.slug for line in cart] == ["promo"]


async def test_total_sum_of_numeric_prices(fresh_db):
    await add_item(USER, "landing")  # 15 000 ₽
    await add_item(USER, "promo")  # 10 000 ₽

    cart = await get_cart(USER)
    total = format_total(cart)

    assert total == "25 000 ₽"


async def test_total_accounts_for_quantity(fresh_db):
    await add_item(USER, "landing-start")  # 8 000 ₽
    await add_item(USER, "landing-start")  # ещё раз -> количество 2

    cart = await get_cart(USER)
    total = format_total(cart)

    assert total == "16 000 ₽"


async def test_total_excludes_individually_priced_items_but_lists_them(fresh_db):
    await add_item(USER, "landing")  # 15 000 ₽, числовая цена
    await add_item(USER, "forms")  # "обсуждается индивидуально"

    cart = await get_cart(USER)
    total = format_total(cart)

    assert "15 000 ₽" in total
    assert "Интеграция форм" in total  # честно указано, что не вошло в сумму


async def test_empty_cart_total_is_zero(fresh_db):
    assert format_total([]) == "0 ₽"
