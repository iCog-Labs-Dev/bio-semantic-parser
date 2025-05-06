def build_prompt(code: str, error_info: str) -> str:
    return f"""
You are an expert in the MeTTa programming language. Your role is to assist users by explaining their syntax errors and suggesting a fix.
You can refer to MeTTa's official documentation for syntax: https://metta-lang.dev/docs/learn/learn.html
Provide short, accurate explanations and fixes.

Here is an example of how to respond:

Example:
  Code:
    (add $x 3
  Error:
    Unclosed parenthesis at position 0
  Response:
    Error: The expression is missing a closing parenthesis.
    Fix: Add a ')' at the end so it reads `(add $x 3)`.

Now please do the same for the following:

Code:
{code}

Error:
{error_info}

Format your answer exactly like the example above:
Error: [explanation]
Fix: [suggested fix]
"""

FOL_generation_prompt = """You are a biomedical text reasoning assistant. Your task is to extract factual relationships from biomedical text in the form of Subject–Predicate–Object (S-P-O) triples.

CRITICAL INSTRUCTIONS:

Concept Restriction: Use only the provided annotations for the subject and object values. Specifically, use the "pretty_name" of the concept. Do not invent new subjects or objects.

Predicate from Context: Derive the predicate from the context of the original text. Use a short verb or verb phrase (1–3 words, ideally 1–2).

Strict JSON Format:

Output only a valid JSON array of triples.

Each triple must be a JSON object with exactly three keys: "subject", "predicate", and "object".

Do not include explanations, markdown tags, or extra text. Only output the raw JSON array.

Lowercase Everything: All values (subject, predicate, object) must be lowercase.

Pronoun Resolution: Replace pronouns with the corresponding concept name from annotations (e.g., "she" → "patients").

Specificity & Completeness:

Be as specific as the text allows (e.g., "breast carcinoma" instead of "carcinoma").

Extract all distinct, factual S-P-O relationships mentioned.

Text:
{texts}

Annotations:
{concepts}

Expected Output (JSON):
```{{
  "triples": [
    {{
      "subject": "Patients",
      "predicate": "diagnosed_with",
      "object": "breast carcinoma"
    }}
  ]
}}```

"""
