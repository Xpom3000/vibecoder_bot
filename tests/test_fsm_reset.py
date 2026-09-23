import asyncio
from types import SimpleNamespace

import pytest


class _DummyMessage:
    def __init__(self, user_id=123, username="me", text: str = ""):
        self.from_user = SimpleNamespace(id=user_id, username=username)
        self.bot = SimpleNamespace()
        self.text = text

    async def answer(self, *args, **kwargs):
        return None


class _DummyCallback:
    def __init__(self, user_id=123):
        self.from_user = SimpleNamespace(id=user_id)
        self.message = SimpleNamespace()

    async def answer(self, *args, **kwargs):
        return None


class _AsyncMock:
    def __init__(self):
        self.called = False

    async def __call__(self, *args, **kwargs):
        self.called = True


@pytest.mark.asyncio
async def test_start_clears_state(monkeypatch):
    from handlers import start as start_module

    state = SimpleNamespace()
    async def finish():
        state.finished = True
    state.finish = finish

    msg = _DummyMessage(user_id=42)

    called = {}

    def fake_clear_history(uid):
        called['uid'] = uid

    monkeypatch.setattr(start_module, "clear_history", fake_clear_history)

    await start_module.start_default(msg, state)

    assert called.get('uid') == 42
    assert getattr(state, 'finished', False) is True


@pytest.mark.asyncio
async def test_showcase_clears_state(monkeypatch):
    from handlers import showcase as showcase_module

    state = SimpleNamespace()
    async def clear():
        state.cleared = True
    state.clear = clear

    msg = _DummyMessage(user_id=7)
    # call handler
    await showcase_module.show_showcase(msg, state)

    assert getattr(state, 'cleared', False) is True


@pytest.mark.asyncio
async def test_brief_finish_on_submit(monkeypatch):
    from handlers import brief as brief_module

    # prepare state mock
    data = {
        'name': 'Anna',
        'project_type': 'Лендинг',
        'task': 'Сайт для фитнеса',
        'contact': '+79990001122',
    }

    state = SimpleNamespace()

    async def update_data(**kwargs):
        return None

    async def get_data():
        return data

    async def finish():
        state.finished = True

    state.update_data = update_data
    state.get_data = get_data
    state.finish = finish

    # monkeypatch external side effects
    called = {}

    async def fake_save_lead(lead):
        called['lead'] = lead

    async def fake_notify_admin(bot, admin_chat, card):
        called['notify'] = True

    monkeypatch.setattr(brief_module, 'save_lead', fake_save_lead)
    monkeypatch.setattr(brief_module, 'notify_admin', fake_notify_admin)

    msg = _DummyMessage(user_id=55, username='anna')
    # invoke handler
    await brief_module.process_contact(msg, state)

    assert getattr(state, 'finished', False) is True
    assert 'lead' in called
    assert called['lead']['name'] == 'Anna'
