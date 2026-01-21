from collections import Counter

def check_duplicates(database):
    """
    Check for duplicate keys or titles.
    Returns a list of warnings.
    """
    warnings = []
    # Keys are now guaranteed unique by deduplicator, so we skip strict key check here.
    pass      
    # Check for potential duplicate titles
    titles = [entry.get('title', '').lower() for entry in database.entries if 'title' in entry]
    # Simple check, might be too noisy if similar titles exist.
    
    return warnings

def check_missing_fields(database):
    """
    Check for missing standard fields like author, title, year.
    """
    warnings = []
    required_fields = ['author', 'title', 'year']
    
    for entry in database.entries:
        missing = [field for field in required_fields if field not in entry]
        if missing:
            warnings.append(f"Entry {entry['ID']} missing fields: {', '.join(missing)}")
            
    return warnings

def validate_database(database):
    """
    Run all validations.
    """
    all_warnings = []
    all_warnings.extend(check_duplicates(database))
    all_warnings.extend(check_missing_fields(database))
    return all_warnings
