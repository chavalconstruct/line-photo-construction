import pytest
from unittest.mock import patch, MagicMock
from linebot.v3.webhooks import TextMessageContent, ImageMessageContent, ContentProvider

from src.webhook_processor import process_webhook_event
from tests.test_helpers import create_mock_event

@pytest.mark.asyncio
@patch('src.webhook_processor.handle_image_message')
@patch('src.webhook_processor.handle_text_message')
async def test_process_webhook_event_routes_to_text_handler(
    mock_text_handler, mock_image_handler
):
    """
    Tests that a TextMessageContent event is correctly routed to the text handler.
    """
    # Arrange
    text_message = TextMessageContent(id="123", text="hello", quote_token="q_token_route_test")
    event = create_mock_event("U123", text_message)
    
    # Act
    await process_webhook_event(
        event, MagicMock(), MagicMock(), MagicMock(),
        MagicMock(), "dummy_token", "dummy_parent_id"
    )

    # Assert
    mock_text_handler.assert_called_once()
    mock_image_handler.assert_not_called()

@pytest.mark.asyncio
@patch('src.webhook_processor.handle_image_message')
@patch('src.webhook_processor.handle_text_message')
async def test_process_webhook_event_routes_to_image_handler(
    mock_text_handler, mock_image_handler
):
    """
    Tests that an ImageMessageContent event is correctly routed to the image handler.
    """
    # Arrange
    image_message = ImageMessageContent(
    id="456",
    quote_token="q_token_route_test",
    content_provider=ContentProvider(type="line")
)
    event = create_mock_event("U456", image_message)

    # Act
    await process_webhook_event(
        event, MagicMock(), MagicMock(), MagicMock(),
        MagicMock(), "dummy_token", "dummy_parent_id"
    )

    # Assert
    mock_text_handler.assert_not_called()
    mock_image_handler.assert_called_once()