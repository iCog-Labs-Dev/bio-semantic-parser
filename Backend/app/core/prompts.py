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

FOL_generation_prompt = """You are a biomedical text reasoning assistant. Your task is to extract relationships from biomedical text and express them in the form of subject–predicate–object triples, formatted as JSON.

Only use concepts from the provided annotations as the **subject** and **object** of each triple. The **predicate** should describe the relationship between them, based on the context of the original text.

Each annotation contains:
- `pretty_name`: a normalized biomedical concept
- `detected_name`: the phrase as it appears in the original text
- `types`: the semantic category of the concept

Use `pretty_name` for the subject and object values. The `detected_name` shows the original wording found in the text but should not appear in the output.

---

### Example

Text:
"The patient was diagnosed with cancer."

Annotations:
- Concept: Patients (Type: Patient or Disabled Group, Mentioned as: "patient")
- Concept: cancer diagnosis (Type: Diagnostic Procedure, Mentioned as: "diagnosed~with~cancer")

Expected Output (JSON):
```{{
  "triples": [
    {{
      "subject": "Patients",
      "predicate": "diagnosed_with",
      "object": "cancer diagnosis"
    }}
  ]
}}```

---

Now, extract triples from the following input:

Text:
{texts}

Annotations:
{concepts}

Expected Output (JSON):
"""
