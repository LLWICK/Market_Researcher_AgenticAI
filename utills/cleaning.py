import re

def clean_output(text: str) -> str:
    if not text:
        return ""
    # Remove chain-of-thought style markers
    text = re.sub(r"(?i)(thoughts?:|reasoning:|analysis:).*", "", text)
    # Remove angle-bracket reasoning tags
    text = re.sub(r"<.*?>", "", text)
    # Remove extra markdown symbols
    text = re.sub(r"[*_#>`~-]+", "", text)
    # Collapse multiple spaces/newlines
    text = re.sub(r"\s+", " ", text).strip()
    return text


from typing import Union, List, Dict

def extract_clean_text(messages: Union[str, List, Dict]) -> str:
    """
    Extract the final assistant-generated text from messy agent outputs.
    Handles raw dicts, lists of messages, or raw event strings.
    """
    if not messages:
        return ""

    text = ""

    # Case 1: If it's already a dict with role/content
    if isinstance(messages, dict) and "content" in messages:
        text = messages["content"]

    # Case 2: If it's a list of messages
    elif isinstance(messages, list):
        assistant_msgs = [m.get("content", "") for m in messages if m.get("role") == "assistant"]
        text = " ".join(assistant_msgs)

    # Case 3: If it's a big raw string
    elif isinstance(messages, str):
        # Try to capture the last assistant content
        match = re.findall(r"role='assistant'.*?content=\"(.*?)\"", messages, flags=re.S)
        if match:
            text = match[-1]  # take last assistant block
        else:
            # fallback: take everything after the last 'assistant'
            if "assistant" in messages:
                text = messages.split("assistant")[-1]

    # Final cleanup
    text = re.sub(r"(?s)metrics=.*", "", text)        # drop metrics blobs
    text = re.sub(r"\s+", " ", text).strip()          # collapse whitespace
    text = re.sub(r"\\n", "\n", text)                 # unescape newlines
    text = re.sub(r"(?i)(thoughts?:|reasoning:).*", "", text)  # drop CoT markers

    return text

