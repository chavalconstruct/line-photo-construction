import pytest
import time
from src.state_manager import StateManager

@pytest.fixture
def state_manager():
    """Provides a clean StateManager instance for each test."""
    # We can define the session duration for testing purposes
    return StateManager(session_duration_seconds=10)

def test_set_and_get_active_group_within_session(state_manager):
    """
    Tests that a group can be retrieved if the session has not expired.
    """
    user_id = "U12345"
    group_name = "Group_A"

    state_manager.set_pending_upload(user_id, group_name)
    active_group = state_manager.get_active_group(user_id)
    assert active_group == group_name

def test_get_active_group_returns_none_if_expired(state_manager):
    """
    Tests that None is returned if the session has expired.
    """
    user_id = "U12345"
    group_name = "Group_A"
    
    # We manually set a timestamp in the past to simulate expiration
    expired_timestamp = time.time() - (state_manager.SESSION_DURATION_SECONDS + 5)
    state_manager._pending_uploads[user_id] = {
        "group": group_name,
        "timestamp": expired_timestamp
    }

    active_group = state_manager.get_active_group(user_id)
    assert active_group is None
    # Also check that the expired session was cleaned up
    assert user_id not in state_manager._pending_uploads


def test_get_active_group_for_non_pending_user(state_manager):
    """
    Tests that getting a state for a user without a session returns None.
    """
    assert state_manager.get_active_group("U_non_existent") is None

def test_set_pending_upload_creates_timestamp(state_manager):
    """
    Tests that setting a pending upload correctly records the timestamp.
    """
    user_id = "U12345"
    group_name = "Group_A"
    
    current_time = time.time()
    state_manager.set_pending_upload(user_id, group_name)

    # Check the internal structure (for testing purposes)
    assert user_id in state_manager._pending_uploads
    session_data = state_manager._pending_uploads[user_id]
    assert session_data['group_name'] == group_name
    # The timestamp should be very close to the current time
    assert session_data['timestamp'] == pytest.approx(current_time, abs=1)

def test_refresh_session_updates_timestamp(state_manager):
    """
    Tests that refreshing a session updates its timestamp to the current time.
    """
    user_id = "U12345"
    group_name = "Group_A"

    # Set an initial state with an old timestamp
    old_timestamp = time.time() - 5
    state_manager._pending_uploads[user_id] = {
        "group": group_name,
        "timestamp": old_timestamp
    }
        
    