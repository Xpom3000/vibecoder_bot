"""Автотесты онлайн-оплаты через ЮKassa.

Реальные HTTP-запросы к ЮKassa НЕ делаются — aiohttp.ClientSession
подменяется моком. Проверяем только свою логику:
- get_exact_total(): точная сумма доступна только когда ВСЕ позиции имеют
  числовую, не приблизительную цену;
- is_payment_confirmed(): True только для статуса "succeeded" от ЮKassa —
  это и есть бизнес-правило "оплачен только при подтверждённом платеже";
- create_payment()/get_payment_status(): корректно разбирают ответ API
  и возвращают None при ошибке/некорректном ответе, не падая.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.cart import CartLine, get_exact_total
from services import yookassa


def _line(slug, price_text, quantity, line_price, is_approx):
    return CartLine(
        slug=slug,
        title=slug,
        price_text=price_text,
        quantity=quantity,
        line_price=line_price,
        is_approx=is_approx,
    )


# --- get_exact_total ---

def test_exact_total_with_only_numeric_prices():
    lines = [
        _line("landing", "15 000 ₽", 1, 15000, False),
        _line("promo", "10 000 ₽", 1, 10000, False),
    ]
    assert get_exact_total(lines) == 25000


def test_exact_total_is_none_when_any_price_is_approximate():
    lines = [
        _line("landing", "15 000 ₽", 1, 15000, False),
        _line("multipage", "от 100 000 ₽", 1, 100000, True),
    ]
    assert get_exact_total(lines) is None


def test_exact_total_is_none_when_any_price_is_individual():
    lines = [
        _line("landing", "15 000 ₽", 1, 15000, False),
        _line("forms", "обсуждается индивидуально", 1, None, False),
    ]
    assert get_exact_total(lines) is None


def test_exact_total_is_none_for_empty_cart():
    assert get_exact_total([]) is None


# --- is_payment_confirmed (ключевое бизнес-правило) ---

@pytest.mark.parametrize(
    "status,expected",
    [
        ("succeeded", True),
        ("pending", False),
        ("waiting_for_capture", False),
        ("canceled", False),
        (None, False),
        ("", False),
    ],
)
def test_is_payment_confirmed_only_for_succeeded(status, expected):
    assert yookassa.is_payment_confirmed(status) is expected


# --- create_payment / get_payment_status: мокаем HTTP, проверяем разбор ответа ---

def _mock_session(response_status: int, response_json: dict):
    """Строит мок aiohttp.ClientSession(...).post(...)/get(...) без единого
    реального сетевого запроса."""
    mock_response = MagicMock()
    mock_response.status = response_status
    mock_response.json = AsyncMock(return_value=response_json)
    mock_response.text = AsyncMock(return_value=str(response_json))

    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    return mock_session


@pytest.mark.asyncio
async def test_create_payment_returns_none_when_not_configured(monkeypatch):
    monkeypatch.setattr(yookassa, "YOOKASSA_SHOP_ID", None)
    monkeypatch.setattr(yookassa, "YOOKASSA_SECRET_KEY", None)

    result = await yookassa.create_payment(1000, "тест", "https://t.me/")
    assert result is None


@pytest.mark.asyncio
async def test_create_payment_parses_successful_response(monkeypatch):
    monkeypatch.setattr(yookassa, "YOOKASSA_SHOP_ID", "test-shop")
    monkeypatch.setattr(yookassa, "YOOKASSA_SECRET_KEY", "test-secret")

    fake_response = {
        "id": "2d4f9c9a-0000-5000-8000-000000000000",
        "confirmation": {"confirmation_url": "https://yoomoney.ru/checkout/pay/xyz"},
    }
    mock_session = _mock_session(200, fake_response)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await yookassa.create_payment(15000, "Заказ №1", "https://t.me/")

    assert result == {
        "id": "2d4f9c9a-0000-5000-8000-000000000000",
        "confirmation_url": "https://yoomoney.ru/checkout/pay/xyz",
    }


@pytest.mark.asyncio
async def test_create_payment_returns_none_on_api_error(monkeypatch):
    monkeypatch.setattr(yookassa, "YOOKASSA_SHOP_ID", "test-shop")
    monkeypatch.setattr(yookassa, "YOOKASSA_SECRET_KEY", "test-secret")

    mock_session = _mock_session(401, {"type": "error", "description": "Invalid credentials"})

    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await yookassa.create_payment(15000, "Заказ №1", "https://t.me/")

    assert result is None


@pytest.mark.asyncio
async def test_get_payment_status_returns_status_string(monkeypatch):
    monkeypatch.setattr(yookassa, "YOOKASSA_SHOP_ID", "test-shop")
    monkeypatch.setattr(yookassa, "YOOKASSA_SECRET_KEY", "test-secret")

    mock_session = _mock_session(200, {"id": "pay_1", "status": "succeeded"})

    with patch("aiohttp.ClientSession", return_value=mock_session):
        status = await yookassa.get_payment_status("pay_1")

    assert status == "succeeded"


@pytest.mark.asyncio
async def test_get_payment_status_returns_none_on_network_error(monkeypatch):
    monkeypatch.setattr(yookassa, "YOOKASSA_SHOP_ID", "test-shop")
    monkeypatch.setattr(yookassa, "YOOKASSA_SECRET_KEY", "test-secret")

    with patch("aiohttp.ClientSession", side_effect=ConnectionError("нет сети")):
        status = await yookassa.get_payment_status("pay_1")

    assert status is None
