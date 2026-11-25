import pytest


@pytest.mark.parametrize("attempt", [1, 2, 3])  # порядок классов на странице меняется
def test_primary_button_click_shows_alert(class_attr_page, attempt):
    class_attr_page.open().click_primary_button()
    assert class_attr_page.accept_alert_text() == "Primary button pressed"
