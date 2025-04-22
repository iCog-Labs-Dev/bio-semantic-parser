# Prompt for Metta syntax
def build_prompt(code: str, error_info: str) -> str:
    return f"""
You are a MeTTa syntax expert. Explain this error and suggest a fix:
Code: {code}
Error: {error_info}
Format: "Error: [description]. Fix: [solution]"
"""
