import pytest


@pytest.mark.parametrize("name", ["My Button", "Автотест", "123"])
def test_button_renamed_after_click(text_input_page, name):
    text_input_page.open().set_button_name(name).click_button()
    assert text_input_page.get_button_text() == name
