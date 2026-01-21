from collections import Counter, defaultdict
from unidecode import unidecode
import re

def normalize_key_text(text):
    """Normalize text for key generation/comparison."""
    if not text:
        return ""
    return unidecode(text).lower().strip()

def get_entry_fingerprint(entry):
    """
    Generate fingerprints for an entry to identify duplicates.
    Returns:
        doi_fp: DOI string (or None)
        content_fp: Tuple of (Title, Author, Year) (or None)
    """
    # 1. DOI Fingerprint
    doi_fp = None
    if 'doi' in entry and entry['doi'].strip():
        doi_fp = normalize_key_text(entry['doi'])
        
    # 2. Content Fingerprint
    content_fp = None
    title = normalize_key_text(entry.get('title', ''))
    # Extract first author
    author_str = normalize_key_text(entry.get('author', ''))
    year = normalize_key_text(entry.get('year', ''))
    
    # We need at least Title + (Author OR Year) to be reasonably certain
    if title and len(title) > 10 and (author_str or year):
        # Simplify title (remove non-alphanumeric)
        simple_title = "".join(filter(str.isalnum, title))
        
        # Simplify author (just first author's last name roughly)
        # "smith, john and doe, jane" -> "smith"
        simple_author = ""
        if author_str:
            parts = author_str.split(' and ')
            if parts:
                first_part = parts[0] # "smith, john"
                if ',' in first_part:
                    simple_author = first_part.split(',')[0].strip()
                else:
                    simple_author = first_part.split(' ')[-1].strip() # "john smith" -> "smith"
        
        content_fp = (simple_title, simple_author, year)
        
    return doi_fp, content_fp

def merge_entries(entries):
    """
    Merge a list of entries into a single entry.
    - Preserves the ID of the first entry (master).
    - Merges fields: if master is missing a field, take from others.
    """
    master = entries[0]
    for other in entries[1:]:
        for key, value in other.items():
            if key not in master or not master[key]:
                master[key] = value
            # Note: We don't overwrite master's non-empty values. 
            # This generally keeps the "first" entry's values, which is usually safe.
    return master

def deduplicate_database(database):
    """
    Identify and merge duplicates.
    Returns:
        database: Modified database
        merged_count: Number of entries removed via merging
    """
    # Group by fingerprints
    doi_groups = defaultdict(list)
    content_groups = defaultdict(list)
    
    entries_by_id = {}
    
    # First pass: Build indices
    for entry in database.entries:
        entries_by_id[entry['ID']] = entry
        doi_fp, content_fp = get_entry_fingerprint(entry)
        
        if doi_fp:
            doi_groups[doi_fp].append(entry['ID'])
        if content_fp:
            content_groups[content_fp].append(entry['ID'])
            
    ids_to_remove = set()
    merged_count = 0
    
    # Process DOI groups first (strongest signal)
    # We want to form sets of IDs that are duplicates
    # This is a disjoint set problem effectively, but let's simplify.
    # Since we are modifying the list at the end, we just track "master" and "removed".
    
    # Helper to process a group of IDs
    def process_group(group_ids):
        # Filter out already removed
        valid_ids = [eid for eid in group_ids if eid not in ids_to_remove]
        if len(valid_ids) < 2:
            return 0
            
        # We found valid duplicates!
        # Sort them to be deterministic? Or just take first.
        # Let's take the one with the most fields as master?
        # For now, just taking the first one in the list order is fine.
        
        master_id = valid_ids[0]
        duplicates_to_merge = [entries_by_id[eid] for eid in valid_ids]
        
        # Merge
        merge_entries(duplicates_to_merge)
        
        # Mark others for removal
        for eid in valid_ids[1:]:
            ids_to_remove.add(eid)
            
        return len(valid_ids) - 1

    # Check DOI groups
    for doi, ids in doi_groups.items():
        if len(ids) > 1:
            merged_count += process_group(ids)
            
    # Check Content groups
    for fp, ids in content_groups.items():
        if len(ids) > 1:
            merged_count += process_group(ids)
            
    # Rebuild database entries list
    if ids_to_remove:
        new_entries = [e for e in database.entries if e['ID'] not in ids_to_remove]
        database.entries = new_entries
        
    return database, merged_count

def uniquify_keys(database):
    """
    Ensure all keys in the database are unique.
    Renames duplicates by appending _a, _b, etc.
    """
    existing_keys = set()
    renamed_count = 0
    
    for entry in database.entries:
        original_key = entry['ID']
        new_key = original_key
        
        if new_key in existing_keys:
            # Generate a unique key
            # Try _a, _b...
            suffix_char_code = 97 # 'a'
            suffix_num = 2
            
            # Formulate a unique key
            # Logic: try _a..._z, then _2..._N
            
            candidate = f"{original_key}_{chr(suffix_char_code)}"
            while candidate in existing_keys:
                suffix_char_code += 1
                if suffix_char_code > 122: # 'z'
                     # Switch to numbers
                     candidate = f"{original_key}_{suffix_num}"
                     suffix_num += 1
                else:
                    candidate = f"{original_key}_{chr(suffix_char_code)}"
            
            new_key = candidate
            entry['ID'] = new_key
            renamed_count += 1
            
        existing_keys.add(new_key)
        
    return database, renamed_count

def check_fuzzy_duplicates(database):
    """
    Check for entries that look similar but were NOT merged (maybe different year? or slight typo).
    This logic is partly redundant with deduplicate_database but useful as a safety check or for weaker matches.
    """
    # For now, since we have aggressive deduplication, we might skip this or keep it for very weak matches.
    # Let's keep a simplified version that warns if TITLES are same but processed as different (e.g. missing year in one).
    warnings = []
    seen_titles = {}
    
    for entry in database.entries:
        if 'title' not in entry: continue
        title = normalize_key_text(entry['title'])
        simple_title = "".join(filter(str.isalnum, title))
        if len(simple_title) < 15: continue
            
        key = entry['ID']
        if simple_title in seen_titles:
            prev_key = seen_titles[simple_title]
            warnings.append(f"Possible duplicate (not merged): '{key}' and '{prev_key}' have similar titles.")
        else:
            seen_titles[simple_title] = key
            
    return warnings

    """
    Ensure all keys in the database are unique.
    If duplicates are found, rename them by appending _a, _b, etc.
    This modifies the database in-place.
    """
    # Bibtexparser load might store duplicates if not careful, but usually it overwrites locally if using dict.
    # However, since we used `common_strings=True`, let's check how bibtexparser stores them. 
    # v1 stores entries in a list `database.entries` (list of dicts).
    
    seen_keys = Counter()
    # First pass to count
    for entry in database.entries:
        seen_keys[entry['ID']] += 1
        
    # If no duplicates, we represent a "set" of keys to track used ones for the renaming process
    # But wait, if we rename, we need to know which instance we are on.
    
    # Actually, simpler approach:
    # Iterate and build a new list of keys.
    existing_keys = set()
    renamed_count = 0
    
    for entry in database.entries:
        original_key = entry['ID']
        new_key = original_key
        
        # If this key has been seen already in THIS pass (meaning it's a duplicate of a previous entry in the list)
        if new_key in existing_keys:
            # Generate a unique key
            suffix_char = 'a'
            while new_key in existing_keys:
                new_key = f"{original_key}_{suffix_char}"
                # Increment suffix: a -> b -> ... -> z -> aa ...
                # Simple implementation: unique integer suffix if simple char fails or just incrementing
                # Let's try simple _2, _3 first as it's clearer
                if new_key in existing_keys:
                     # try numbered
                     i = 2
                     while f"{original_key}_{i}" in existing_keys:
                         i += 1
                     new_key = f"{original_key}_{i}"
            
            entry['ID'] = new_key
            renamed_count += 1
            
        existing_keys.add(new_key)
        
    return database, renamed_count

def check_fuzzy_duplicates(database):
    """
    Check for entries that look similar (same title/author) but have different keys.
    Returns a list of warning strings.
    """
    warnings = []
    
    # Normalized representation -> keys
    # We use (normalized_title) as signature
    seen_titles = {}
    
    for entry in database.entries:
        if 'title' not in entry:
            continue
            
        title = unidecode(entry['title']).lower().strip()
        # Remove non-alphanumeric for better matching
        simple_title = "".join(filter(str.isalnum, title))
        
        if len(simple_title) < 10: # Skip very short titles
            continue
            
        key = entry['ID']
        
        if simple_title in seen_titles:
            prev_key = seen_titles[simple_title]
            warnings.append(f"Potential duplicate content: '{key}' looks similar to '{prev_key}' (Title: {entry['title'][:50]}...)")
        else:
            seen_titles[simple_title] = key
            
    return warnings
