import re
from app.utils.checkMettaCode import validate_metta_syntax

def convert_predicate_to_metta(predicate_str: str) -> str:
    """
    Converts a FOL-like string 'predicate(subject, object)' to MeTTa syntax: '(predicate subject object)'
    """
    
    pattern = r'^([a-zA-Z_][\w]*)\((.+?),\s*(.+)\)$'
    match = re.match(pattern, predicate_str.strip())

    if match:
        predicate, subject, obj = match.groups()

        def sanitize(atom: str) -> str:
            return (
                atom.strip()
                .replace(" ", "_")
                .replace(",", "_")
                .replace("(", "")
                .replace(")", "")
                .replace('"', '')
            )

        predicate = sanitize(predicate)
        subject = sanitize(subject)
        obj = sanitize(obj)

        return f"({predicate} {subject} {obj})"
    else:
        return f"; Invalid format: {predicate_str}"

def convert_all_to_metta(predicates: list[str]) -> list[str]:
    return [convert_predicate_to_metta(p) for p in predicates]


def validate_metta_lines(metta_lines: list[str]) -> list[str]:
    """
    Returns only syntactically valid MeTTa lines
    """
    return [line for line in metta_lines if validate_metta_syntax(line)[0]]
