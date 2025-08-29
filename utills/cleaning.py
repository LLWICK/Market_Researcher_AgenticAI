# utils.py
def clean_response(resp):
    """
    Extracts clean text from phi/LLM responses.
    Works whether resp is RunResponse, dict, or plain str.
    """
    # Case 1: response has `.output_text`
    if hasattr(resp, "output_text"):
        return resp.output_text.strip() 

    # Case 2: response has `.content`
    if hasattr(resp, "content") and isinstance(resp.content, str):
        return resp.content.strip()

    # Case 3: response is dict with 'summary' or 'insights' etc.
    if isinstance(resp, dict):
        for key in ["summary", "insights", "trends", "content"]:
            if key in resp:
                return str(resp[key]).strip()

    # Case 4: raw string
    if isinstance(resp, str):
        return resp.strip()

    # Fallback: dump as string
    return str(resp)
