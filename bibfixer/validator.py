from collections import Counter

def check_duplicates(database):
    """
    Check for duplicate keys or titles.
    Returns a list of warnings.
    """
    warnings = []
    doi_map = {}
    title_map = {}

    for entry in database.entries:
        doi = entry.get("doi", "").strip().lower()
        if doi:
            doi_map.setdefault(doi, []).append(entry["ID"])

        title = entry.get("title", "").strip().lower()
        year = entry.get("year", "").strip().lower()
        if title:
            title_key = (title, year)
            title_map.setdefault(title_key, []).append(entry["ID"])

    for doi, ids in doi_map.items():
        if len(ids) > 1:
            warnings.append(f"Duplicate DOI {doi} found in entries: {', '.join(ids)}")

    for (title, year), ids in title_map.items():
        if len(ids) > 1:
            label = f"{title[:50]}..."
            if year:
                label = f"{label} ({year})"
            warnings.append(f"Duplicate title detected: {label} in entries: {', '.join(ids)}")

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
