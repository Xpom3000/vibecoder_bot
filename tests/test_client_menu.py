from keyboards.reply import BTN_CART, BTN_CONTACT_HUMAN, BTN_SHOWCASE, BTN_STAGES, persistent_menu


def test_client_menu_has_four_required_buttons():
    markup = persistent_menu()
    labels = [button.text for row in markup.keyboard for button in row]

    assert labels == [
        BTN_SHOWCASE,
        BTN_CART,
        BTN_CONTACT_HUMAN,
        BTN_STAGES,
    ]
    assert BTN_SHOWCASE == "🛍 Витрина"
    assert BTN_CART == "� Корзина"
    assert BTN_CONTACT_HUMAN == "🙋 Поддержка"
    assert BTN_STAGES == "🗺 Этапы работы"
