"""
Utility functions for handling AutoGen responses and common operations.
"""


def extract_text_from_autogen_response(response) -> str:
    """
    Extract text content from various AutoGen response objects.

    Handles TaskResult, ChatMessage, and other AutoGen response types uniformly.

    Args:
        response: AutoGen response object (TaskResult, ChatMessage, etc.) or string

    Returns:
        str: Extracted text content
    """
    if isinstance(response, str):
        return response

    # Handle TaskResult object
    if hasattr(response, "messages") and len(response.messages) > 0:
        last_message = response.messages[-1]
        if hasattr(last_message, "content"):
            return last_message.content
        else:
            return str(last_message)

    # Handle ChatMessage or other response objects
    if hasattr(response, "chat_message"):
        chat_msg = response.chat_message
        if hasattr(chat_msg, "content"):
            return chat_msg.content
        elif hasattr(chat_msg, "to_text"):
            return chat_msg.to_text()
        else:
            return str(chat_msg)

    # Handle direct content attribute
    if hasattr(response, "content"):
        return response.content

    # Fallback to string conversion
    return str(response)
