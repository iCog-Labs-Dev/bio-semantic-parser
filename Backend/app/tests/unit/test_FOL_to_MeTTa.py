from app.services.fol_to_metta import (
    convert_predicate_to_metta,
    convert_all_to_metta,
    split_predicates,
)

def test_convert_predicate_to_metta_two_args():
    assert convert_predicate_to_metta("likes(Alice, Bob)") == "(likes Alice Bob)"

def test_convert_predicate_to_metta_one_arg():
    assert convert_predicate_to_metta("Organism(DrosophilaMelanogaster)") == "(Organism DrosophilaMelanogaster)"

def test_convert_predicate_to_metta_invalid():
    assert convert_predicate_to_metta("InvalidFormat") == "; Invalid format: InvalidFormat"

def test_convert_all_to_metta():
    input_preds = ["likes(Alice, Bob)", "Organism(Drosophila)"]
    expected = ["(likes Alice Bob)", "(Organism Drosophila)"]
    assert convert_all_to_metta(input_preds) == expected

def test_split_predicates():
    text = "likes(Alice, Bob) Organism(Drosophila) Parent(joshua, Mike)"
    result = split_predicates(text)
    assert result == ["likes(Alice, Bob)", " Organism(Drosophila)", " Parent(joshua, Mike)"]
