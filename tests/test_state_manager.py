import pytest
from src.state_manager import StateManager

@pytest.fixture
def state_manager():
    """Provides a clean StateManager instance for each test."""
    return StateManager()

def test_set_and_consume_pending_upload(state_manager):
    """
    Tests that we can set a user's pending state and then consume it,
    which should return the group name and clear the state.
    """
    user_id = "U12345"
    group_name = "Group_A"

    # Set the pending state
    state_manager.set_pending_upload(user_id, group_name)

    # Consume the state
    consumed_group = state_manager.consume_pending_upload(user_id)

    # Assert that we got the correct group name
    assert consumed_group == group_name

    # Assert that the state is now cleared
    assert state_manager.consume_pending_upload(user_id) is None

def test_consume_pending_upload_for_non_pending_user(state_manager):
    """
    Tests that consuming a state for a user who has not sent a
    secret code returns None.
    """
    user_id = "U67890"

    # Attempt to consume a non-existent state
    consumed_group = state_manager.consume_pending_upload(user_id)

    # Assert that the result is None
    assert consumed_group is None