from .io import load_bib, save_bib
from .cleaner import clean_database
from .enricher import enrich_database
from .validator import validate_database
from .deduplicator import uniquify_keys, check_fuzzy_duplicates, deduplicate_database
from tqdm import tqdm

def fix_bibliography(input_file, output_file=None):
    """
    Main function to fix a bibliography file.
    
    Args:
        input_file (str): Path to input .bib file.
        output_file (str): Path to output .bib file.
    """
    if output_file is None:
        if input_file.endswith('.bib'):
            output_file = input_file[:-4] + '_fix.bib'
        else:
            output_file = input_file + '_fix.bib'

    print(f"Loading {input_file}...")
    db = load_bib(input_file)
    print(f"Loaded {len(db.entries)} entries.")
    
    # Validation before
    # warnings_before = validate_database(db)
    # if warnings_before:
    #     print("Warnings before processing:")
    #     for w in warnings_before[:10]:
    #         print(f"  - {w}")
    #     if len(warnings_before) > 10:
    #         print(f"  ... and {len(warnings_before) - 10} more.")

    print("Cleaning entries...")
    db = clean_database(db)
    
    print("Smart deduplicating (merging certain duplicates)...")
    db, merged_count = deduplicate_database(db)
    if merged_count > 0:
        print(f"Merged and removed {merged_count} duplicate entries.")
    
    print("Uniquifying keys (renaming remaining ID collisions)...")
    db, renamed_count = uniquify_keys(db)
    if renamed_count > 0:
        print(f"Renamed {renamed_count} duplicate keys to ensure uniqueness.")

    print("Enriching with DOIs (this may take a while)...")
    db, modified_count = enrich_database(db, pbar=tqdm)
    print(f"Added/Updated DOIs for {modified_count} entries.")
    
    # Validation after
    warnings = validate_database(db)
    # Check fuzzy too
    fuzzy_warnings = check_fuzzy_duplicates(db)
    warnings.extend(fuzzy_warnings)
    
    if warnings:
        print("Validation Warnings:")
        for w in warnings[:10]:
            print(f"  - {w}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more.")
            
    print(f"Saving to {output_file}...")
    save_bib(db, output_file)
    print("Done.")
