from .io import load_bib, save_bib
from .cleaner import clean_database
from .enricher import enrich_database
from .validator import validate_database
from .deduplicator import uniquify_keys, check_fuzzy_duplicates, deduplicate_database
from tqdm import tqdm
import os

def fix_bibliography(input_file, output_file=None, verify=False):
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
    
    print("Uniquifying keys (renaming initial ID collisions)...")
    db, renamed_count = uniquify_keys(db)
    if renamed_count > 0:
        print(f"Renamed {renamed_count} duplicate keys to ensure uniqueness.")

    print("Smart deduplicating (merging certain duplicates)...")
    db, merges = deduplicate_database(db)
    merged_count = sum(len(m[1]) for m in merges)
    if merged_count > 0:
        print(f"Merged and removed {merged_count} duplicate entries.")

    print("Enriching with DOIs (this may take a while)...")
    db, enriched_items, verify_log = enrich_database(db, pbar=tqdm, verify=verify)
    print(f"Added/Updated DOIs for {len(enriched_items)} entries.")
    
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
    
    # Generate Report
    report_lines = []
    report_lines.append(f"# Bibliography Fix Report for `{os.path.basename(input_file)}`")
    
    if merges:
        report_lines.append("\n## Merged Entries")
        for master, removed in merges:
            removed_str = ", ".join(removed)
            report_lines.append(f"- {removed_str} -> **{master}**")
            
    if enriched_items:
        report_lines.append("\n## Added DOIs")
        for eid, doi in enriched_items:
            report_lines.append(f"- **{eid}**: {doi}")
            
    if not merges and not enriched_items:
        report_lines.append("\nNo modifications were made.")
        
    report_content = "\n".join(report_lines)
    report_file = output_file + ".report.md"
    if output_file.endswith(".bib"):
        report_file = output_file[:-4] + "_report.md"
        
    with open(report_file, "w") as f:
        f.write(report_content)

    print(f"Report saved to {report_file}")

    if verify and verify_log:
        verify_file = output_file + ".verify.md"
        if output_file.endswith(".bib"):
            verify_file = output_file[:-4] + "_verify.md"
        with open(verify_file, "w") as f:
            f.write("\n".join(verify_log))
        print(f"Verification log saved to {verify_file}")
    print("Done.")
