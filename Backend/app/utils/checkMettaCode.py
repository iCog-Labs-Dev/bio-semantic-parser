import requests
import re
from core.prompts import build_prompt
from core.config import config


def tokenize(code: str):
    """Tokenize MeTTa code into a list of atoms and parentheses."""
    return re.findall(r'\(|\)|[^\s()]+', code)

def is_valid_atom(atom: str) -> bool:
    """Check if an atom is valid based on MeTTa rules."""
    if re.match(r'^\$[\w\-]+$', atom):  
        return True
    if re.match(r'^-?\d+(\.\d+)?$', atom):  
        return True
    if re.match(r'^[a-zA-Z_+\-*/=<>!][\w\-]*$', atom):  
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
    # For now don`t use this one, it will used for to suggest to user how to fix metta syntax
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers)
    return response.json()['choices'][0]['message']['content'].strip()
   



def validate_metta_block(code_block: str) -> bool:
     for block in code_block.strip().splitlines():
        is_valid, error= validate_metta_syntax(block)
        if not is_valid:
            # print(block)
            # print(f"error:{block}, suggestion: {(explain_metta_error_groq(block,error))}")
            return is_valid


     return is_valid
     


    


# test_cases = """
# (a b c)
# (a (b c) d)
# (  a   ( b   c )  )
# ((add $x 3))
# !(equal (add $x 3) 5)
# (a b c)
# (a (b c) d)
# (  a   ( b   c )  )
# (A b c)
# ((add $x 3))
# !(equal (add $x 3) 5)
# (a b c)
# (a (b c) d)
# (  a   ( b   c )  )
# (A b c)
# ((add $x 3))
# !(equal (add $x 3) 5)
# (a b c )
# (a (b c) d)
# (  a   ( b   c )  )
# ((add $x 3))
# !(equal (add $x 3) 5)
# (=(duplicate $x) ($x $x))
# ! (duplicate A)
# ! (duplicate 1.05)


# """ 


# print(validate_metta_block(test_cases))

