import re
from unidecode import unidecode

def normalize_string(string):
    """Normalize strings to ascii, handling some latex/unicode issues."""
    if not string:
        return ""
    # string = re.sub(r'[{}\\\'"^]',"", string) # This might be too aggressive if we want to keep some structure
    # A gentler approach: remove specific control chars or surrounding braces if needed.
    # For now, let's just unidecode to ensure ASCII compatibility if that's desired, 
    # but strictly speaking bibtex supports utf8 now. The user said "clean them".
    # We will strip extra whitespaces.
    string = re.sub(r"\s+", " ", string.strip())
    return string

def clean_entry(entry):
    """
    Clean a single bibliography entry.
    - Remove empty fields.
    - Strip whitespace from values.
    """
    cleaned = {}
    for key, value in entry.items():
        if value is None:
            continue
        valid_val = normalize_string(str(value))
        if valid_val:
            cleaned[key] = valid_val
            
    # Standardize specific fields if needed
    if 'doi' in cleaned:
        # Cleanup DOI: remove URL or "doi:" prefixes, normalize case.
        doi = cleaned['doi'].strip()
        doi = re.sub(r'^(https?://(dx\.)?doi\.org/)', '', doi, flags=re.IGNORECASE)
        doi = re.sub(r'^doi:\s*', '', doi, flags=re.IGNORECASE)
        cleaned['doi'] = doi.lower()
        
    return cleaned

def clean_database(database):
    """
    Apply cleaning to all entries in the database.
    """
    cleaned_entries = []
    for entry in database.entries:
        cleaned_entries.append(clean_entry(entry))
    database.entries = cleaned_entries
    return database
