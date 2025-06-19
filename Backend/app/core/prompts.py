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


predicate_instruction = """Introduction and Goal:

The primary goal of this task is to systematically extract and standardize predicates from the metadata of GSE (Gene Expression Omnibus Series) and GSM (Gene Expression Omnibus Samples) descriptions. 
These predicates will be used to automate the metadata standardization process across various genomics datasets, facilitating efficient and consistent data analysis for meta-studies. 
By defining clear predicates based on experimental design and sample collection, we aim to create a structured queryable framework that enhances data retrieval and analysis capabilities in biological research databases.

Task Description:

Generate a comprehensive list of predicates focused on {aspect} from GSE and GSM descriptions. Ensure each predicate is standardized, uses controlled vocabulary, and adheres strictly to the concepts outlined in the provided guidelines. 
This structured extraction will enable automated systems to better understand and categorize data entries, significantly improving the accuracy and speed of meta-analyses.

Guidelines:
Focus on Key Concepts from the following list:
{aspect_details}

Ensure that the list of predicates is comprehensive and covers all concepts from the list above. 


Define Predicates:

For each identified relationship or attribute, define a predicate. Ensure the predicate name is descriptive of the relationship or attribute it represents.
Create separate predicates for distinctive properties not entailed with each other (for example, strain and age).
Avoid using free-text entries in the predicates.
Exclude predicates that are not related to the specified key concepts. Avoid including predicates related to the following aspects: {irrelevant_aspects_combined}.
Only include predicates relevant to {aspect}. 
Do not generate predicates for generic attributes such as age or sex unless explicitly related to the sample characteristics described in the guidelines.
Do not generate predicates for quantitative measures such as temporal data, dosage, concentration, volume, mass, temperature, speed, time duration, and frequency. These formats are already standardized and provided. Focus on other attributes and relationships related to the specified key concepts.



Standardize Quantitative Data:

Ensure that quantitative data is standardized in a consistent format, such as TimeFrame(value, unit).
Use the following formats for other quantitative measures:
List of Standardized Quantitative Measures
Temporal Data

Format: TimeFrame(value, unit)
Example: TimeFrame(32, Years)
Range Format: TimeFrame(Range(minValue, maxValue), unit)
Range Example: TimeFrame(Range(32, 39), Years)
Dosage

Format: Dosage(value, unit)
Example: Dosage(1.0, gPerKg)
Range Format: Dosage(Range(minValue, maxValue), unit)
Range Example: Dosage(Range(0.5, 1.0), gPerKg)
Concentration

Format: Concentration(value, unit)
Example: Concentration(0.1, Molar)
Range Format: Concentration(Range(minValue, maxValue), unit)
Range Example: Concentration(Range(0.05, 0.1), Molar)
Volume

Format: Volume(value, unit)
Example: Volume(10, mL)
Range Format: Volume(Range(minValue, maxValue), unit)
Range Example: Volume(Range(5, 10), mL)
Mass

Format: Mass(value, unit)
Example: Mass(2.5, mg)
Range Format: Mass(Range(minValue, maxValue), unit)
Range Example: Mass(Range(1.0, 2.5), mg)
Temperature

Format: Temperature(value, unit)
Example: Temperature(37, Celsius)
Range Format: Temperature(Range(minValue, maxValue), unit)
Range Example: Temperature(Range(35, 37), Celsius)
Speed

Format: Speed(value, unit)
Example: Speed(100, rpm)
Range Format: Speed(Range(minValue, maxValue), unit)
Range Example: Speed(Range(80, 100), rpm)
Time Duration

Format: Duration(value, unit)
Example: Duration(30, Minutes)
Range Format: Duration(Range(minValue, maxValue), unit)
Range Example: Duration(Range(20, 30), Minutes)
Frequency

Format: Frequency(value, unit)
Example: Frequency(3, perDay)
Range Format: Frequency(Range(minValue, maxValue), unit)
Range Example: Frequency(Range(2, 3), perDay)

Standardize Software versions:
Ensure that versions of the software related to {aspect} are standardized in a consistent format.
Use the following predicate:
Format: SoftwareVersion(softwareTitle, versionNumber)
Example: SoftwareVersion(AffymetrixPowerTools, 1.12.0)

Format the Output:

Generate a list of predicates.
Provide a brief description of what each predicate represents.
Include an example for each predicate.
Refrain from using sample as an argument in predicates.
Output nothing but a list of predicates according to the provided format. Start right away with the definition of the first predicate.

Output format example:

Definition: somePredicate(argument)
Description: some predicate given for example. Actual predicates will have a meaningful description here.
Example: somePredicate(ExampleArgument)
"""

refinement_prompt = """You are given multiple lists of predicates extracted from various sets of GSE (Gene Expression Omnibus Series) and GSM (Gene Expression Omnibus Samples) metadata descriptions. These predicates are related to {aspect}. Your task involves several key steps to refine and consolidate these predicates into a single, standardized list:

Merge and Deduplicate: Combine all the provided lists into one unified list. Identify and remove any duplicate predicates, ensuring that synonyms and nearly identical concepts are consolidated into a single entry. Aim for a clean, non-redundant list that captures the essence of each predicate without repetition.

fill the values with actual values from the following metadata: {metadata}

Standardize Format and Terminology: Review the merged list for consistency in naming conventions, formatting, and descriptions. Adjust the predicates to ensure they align with the standardized formats discussed in the guidelines. This includes using controlled vocabulary and adhering to a consistent structural format. Use adjustment examples below.

Adjustment examples:
Before: somePredicate("free text argument")
After: somePredicate(VariableLikeArgument)

Before: somePredicate(Argument With Spaces)
After: somePredicate(ArgumentWithoutSpaces)

Before: somePredicate(argument_with_underscore)
After: somePredicate(CamelCaseArgument)

Validate and Refine: Ensure that each predicate in the list strictly pertains to the key concepts of {aspect}. Remove any predicates that do not conform to these guidelines or that address unrelated topics such as the following: {irrelevant_aspects_combined}. Focus on refining predicates to be as specific and relevant as possible.

Format the Final Output: Organize the final list of predicates into a structured format, with definition of each predicate followed by its brief, clear description and an example of usage. Output nothing but a list of predicates in the format specified below. Start with definition of the first predicate right away.

Output Format:  
   Return only the list of refined predicates, one per line, each in the format:  
   `predicateName(<<METADATA_VALUES>>)`  
   Do not include definitions, explanations, or any other commentary. Only return the final list of predicates.


"""

column_name_prompt = """
    You are a data standardization expert. Convert the following dataset column names into standardized predicate names:
    {columns}
    Return a JSON dictionary where keys are original column names and values are standardized predicate names.
    """