"""FSM-состояния формы брифа."""
from aiogram.fsm.state import State, StatesGroup


class BriefForm(StatesGroup):
    name = State()
    project_type = State()
    task = State()
    contact = State()
