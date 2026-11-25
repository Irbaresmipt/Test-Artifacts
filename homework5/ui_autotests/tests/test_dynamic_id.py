def test_button_found_despite_dynamic_id(dynamic_id_page):
    """Кнопка находится по тексту, хотя её id меняется при каждой загрузке."""
    dynamic_id_page.open()
    first_id = dynamic_id_page.get_button_id()
    dynamic_id_page.click_button()

    dynamic_id_page.open()
    second_id = dynamic_id_page.get_button_id()
    dynamic_id_page.click_button()

    assert first_id != second_id, "id должен меняться между загрузками"
