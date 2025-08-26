import pytest
from src.command_parser import parse_command

def test_parse_add_command():
    """Tests parsing a valid 'add' command."""
    text = "add code #s-new for group MyNewGroup"
    expected = {'action': 'add', 'code': '#s-new', 'group': 'MyNewGroup'}
    assert parse_command(text) == expected

def test_parse_add_command_with_different_casing():
    """Tests that parsing is case-insensitive for keywords."""
    text = "Add Code #s-new For Group MyNewGroup"
    expected = {'action': 'add', 'code': '#s-new', 'group': 'MyNewGroup'}
    assert parse_command(text) == expected

def test_parse_remove_command():
    """Tests parsing a valid 'remove' command."""
    text = "remove code #s-old"
    expected = {'action': 'remove', 'code': '#s-old'}
    assert parse_command(text) == expected

def test_parse_remove_command_with_different_casing():
    """Tests case-insensitivity for the 'remove' command."""
    text = "Remove Code #s-old"
    expected = {'action': 'remove', 'code': '#s-old'}
    assert parse_command(text) == expected

def test_parse_invalid_command_format():
    """Tests that malformed commands return None."""
    assert parse_command("add code #s-new") is None  # Missing 'for group'
    assert parse_command("remove #s-old") is None      # Missing 'code'
    assert parse_command("delete code #s-old") is None # Invalid action

def test_parse_non_command_text():
    """Tests that regular text or secret codes are not parsed as commands."""
    assert parse_command("hello world") is None
    assert parse_command("#s1") is None
    assert parse_command("some random text") is None