from keyboards.reply import BTN_CONTACT_HUMAN, BTN_PROJECTS, BTN_SERVICES, BTN_STAGES, BTN_BRIEF, persistent_menu


def test_client_menu_matches_admin_flow():
    markup = persistent_menu()
    labels = [button.text for row in markup.keyboard for button in row]

    assert "📁 Проекты" in labels
    assert "🛠 Услуги" in labels
    assert "🗺 Этапы работы" in labels
    assert "📝 Хочу бриф" in labels
    assert "🙋 Поддержка" in labels
    assert BTN_CONTACT_HUMAN == "🙋 Поддержка"
    assert BTN_PROJECTS == "📁 Проекты"
    assert BTN_SERVICES == "🛠 Услуги"
    assert BTN_STAGES == "🗺 Этапы работы"
    assert BTN_BRIEF == "📝 Хочу бриф"
