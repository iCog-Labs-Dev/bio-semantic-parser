import requests
import re
from core.prompts import build_prompt
from core.config import config



def tokenize(code: str):
    """Tokenize MeTTa code into a list of atoms and parentheses."""
    return re.findall(r'\(|\)|[^\s()]+', code)

def is_valid_atom(atom: str) -> bool:
    """Check if an atom is valid based on MeTTa rules."""
    if re.match(r'^\?[\w\-]+$', atom):  
        return True
    if re.match(r'^-?\d+(\.\d+)?$', atom):  
        return True
    if re.match(r'^[a-z_+\-*/=<>!][\w\-]*$', atom):  
        return True
    return False

def validate_metta_syntax(code: str) -> (bool, str):
    """Validate the syntax of MeTTa code and return (is_valid, explanation)."""
    if not code.strip():
        return False, "Code is empty or contains only whitespace"

    tokens = tokenize(code)
    stack = []
    error_info = None

    for idx, token in enumerate(tokens):
        if token == '(':
            stack.append((token, idx))
        elif token == ')':
            if not stack:
                error_info = f"Unexpected ')' at position {idx} (no matching opening parenthesis)"
                return False, error_info
            stack.pop()
        else:
            if not is_valid_atom(token):
                error_info = f"Invalid atom '{token}' at position {idx}"
                return False, error_info

    if stack:
        error_info = f"Unclosed parenthesis at positions: {[pos for _, pos in stack]}"
        return False, error_info

    return True, "Syntax is valid"



def explain_metta_error_groq(code: str, error_info: str) -> str:
    
    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = build_prompt(code, error_info)

    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers)
    return response.json()['choices'][0]['message']['content'].strip()
   



# test


# test_cases = [
#     ("a"),
#     ("(a b c)"),
#     ("(a (b c) d)"),
#     ("(  a   ( b   c )  )"),
#     ("(a (b c)"),
#     ("(A b c)"),
#     ("123"),
#     ("a)"),
#     ("a-b"),
#     ("(a (B) c)"),
#     (""),
#     ("equal (add ?x 3) 5")
# ]

# if __name__ == "__main__":
#     for code in test_cases:
#         is_valid, error = validate_metta_syntax(code)
#         result = is_valid 

#         print(f"Test: {repr(code)}")
#         print(f"Got: {is_valid}")
#         if not is_valid:
#             print(f"❌ Error: {error}")
#             print(f"🧠 LLM Suggestion: {(code, error)}")
#         else:
#             print("✅ Pass\n" if result else "❌ Fail\n")




