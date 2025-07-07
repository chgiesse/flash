import sys
import time
from multiprocessing import Lock

import pytest
from flaky import flaky

from tests.utils import is_dash_async
from .utils import setup_background_callback_app


def test_001ab_arbitrary(dash_duo, manager):
    if not is_dash_async():
        return
    with setup_background_callback_app(manager, "app_arbitrary_async") as app:
        dash_duo.start_server(app)

        dash_duo.wait_for_text_to_equal("#output", "initial")
        # pause for sync
        time.sleep(0.2)
        dash_duo.find_element("#start").click()

        dash_duo.wait_for_text_to_equal("#secondary", "first")
        dash_duo.wait_for_style_to_equal(
            "#secondary", "background-color", "rgba(255, 0, 0, 1)"
        )
        dash_duo.wait_for_text_to_equal("#output", "initial")
        dash_duo.wait_for_text_to_equal("#secondary", "second")
        dash_duo.wait_for_text_to_equal("#output", "completed")

        dash_duo.find_element("#start-no-output").click()

        dash_duo.wait_for_text_to_equal("#no-output", "started")
        dash_duo.wait_for_text_to_equal("#no-output", "completed")


@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="Python 3.6 long callbacks tests hangs up"
)
@flaky(max_runs=3)
def test_002ab_basic(dash_duo, manager):
    """
    Make sure that we settle to the correct final value when handling rapid inputs
    """
    if not is_dash_async():
        return
    lock = Lock()
    with setup_background_callback_app(manager, "app1_async") as app:
        dash_duo.start_server(app)
        dash_duo.wait_for_text_to_equal("#output-1", "initial value", 15)
        input_ = dash_duo.find_element("#input")
        # pause for sync
        time.sleep(0.2)
        dash_duo.clear_input(input_)

        for key in "hello world":
            with lock:
                input_.send_keys(key)

        dash_duo.wait_for_text_to_equal("#output-1", "hello world", 8)

    assert not dash_duo.redux_state_is_loading
    assert dash_duo.get_logs() == []
