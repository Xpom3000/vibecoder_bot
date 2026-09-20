"""История диалога для контекста в свободных вопросах (services/ai.py).

Хранит последние ~20 сообщений на пользователя (реплики пользователя и
ответы бота вперемешку, в порядке хронологии), чтобы DeepSeek видел не
только последний вопрос, а весь недавний разговор — например, чтобы понять
"а сколько это будет стоить?" после предыдущего вопроса про услугу.

Хранится в памяти процесса (не в БД): при перезапуске бота история
обнуляется. Для чат-бота такого масштаба это осознанное упрощение — полная
персистентность истории диалога не была нужна и добавила бы сложность без
явной необходимости.
"""
from collections import defaultdict, deque

MAX_MESSAGES = 20

_HISTORY: dict[int, deque[dict]] = defaultdict(lambda: deque(maxlen=MAX_MESSAGES))


def get_history(user_id: int) -> list[dict]:
    """Возвращает копию истории пользователя: список {"role", "content"}."""
    return list(_HISTORY[user_id])


def add_message(user_id: int, role: str, content: str) -> None:
    """Добавляет одну реплику в историю. Старые сообщения вытесняются сами
    (deque с maxlen), когда набирается больше MAX_MESSAGES."""
    _HISTORY[user_id].append({"role": role, "content": content})


def clear_history(user_id: int) -> None:
    """Сбрасывает историю — например, при новом /start (новый разговор)."""
    _HISTORY.pop(user_id, None)
