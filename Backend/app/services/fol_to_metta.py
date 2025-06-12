import re
from app.utils.checkMettaCode import validate_metta_syntax

def convert_predicate_to_metta(predicate_str: str) -> str:
    """
    Converts FOL-like predicates to MeTTa syntax.
    Supports both:
      - predicate(subject, object) → (predicate subject object)
      - predicate(argument)       → (predicate argument)
    """

    def sanitize(atom: str) -> str:
        return (
            atom.strip()
            .replace(" ", "_")
            .replace(",", "_")
            .replace("(", "")
            .replace(")", "")
            .replace('"', '')
        )

    predicate_str = predicate_str.strip()

    # Match 2-argument form: predicate(arg1, arg2)
    match_two_args = re.match(r'^([a-zA-Z_][\w]*)\((.+?),\s*(.+)\)$', predicate_str)
    if match_two_args:
        predicate, subject, obj = match_two_args.groups()
        return f"({sanitize(predicate)} {sanitize(subject)} {sanitize(obj)})"

    # Match 1-argument form: predicate(arg)
    match_one_arg = re.match(r'^([a-zA-Z_][\w]*)\((.+)\)$', predicate_str)
    if match_one_arg:
        predicate, arg = match_one_arg.groups()
        return f"({sanitize(predicate)} {sanitize(arg)})"

    # Invalid format
    return f"; Invalid format: {predicate_str}"

def convert_all_to_metta(predicates: list[str]) -> list[str]:
    return [convert_predicate_to_metta(p) for p in predicates]


def validate_metta_lines(metta_lines: list[str]) -> list[str]:
    """
    Returns only syntactically valid MeTTa lines
    """
    return [line for line in metta_lines if validate_metta_syntax(line)[0]]

def split_predicates(text_block: str):
    pattern = r'[a-zA-Z_ ]+\([^()]*\)'
    return re.findall(pattern, text_block)
