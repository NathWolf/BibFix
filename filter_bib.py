#!/usr/bin/env python3
import argparse
import os
import sys

# Add the current directory to python path so we can import bibfixer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bibfixer.io import load_bib, save_bib
from bibfixer.texfilter import extract_citation_keys, filter_database_by_keys


import difflib

def main():
    parser = argparse.ArgumentParser(
        description="Filter a .bib file to only entries cited in a .tex file."
    )
    parser.add_argument("bib_file", help="Path to input .bib file")
    parser.add_argument("tex_file", help="Path to .tex file with citations")
    parser.add_argument("-o", "--output", help="Path to output .bib file", default=None)

    args = parser.parse_args()

    if args.output is None:
        if args.bib_file.endswith(".bib"):
            output_file = args.bib_file[:-4] + "_cited.bib"
        else:
            output_file = args.bib_file + "_cited.bib"
    else:
        output_file = args.output

    print(f"Loading {args.bib_file}...")
    db = load_bib(args.bib_file)
    print(f"Loaded {len(db.entries)} entries.")

    # Get all available keys in the bib file
    available_keys = {entry["ID"] for entry in db.entries}

    keys, include_all = extract_citation_keys(args.tex_file)
    if include_all:
        print("Found \\nocite{*}; keeping all entries.")
    else:
        print(f"Found {len(keys)} cited keys.")

    db, missing = filter_database_by_keys(db, keys, include_all=include_all)
    print(f"Remaining entries: {len(db.entries)}")

    # Generate Alerts Report
    report_path = output_file + "_alerts.md"
    if output_file.endswith(".bib"):
        report_path = output_file[:-4] + "_alerts.md"
    
    report_lines = []
    report_lines.append(f"# Citation Alerts for `{os.path.basename(args.tex_file)}`")
    
    if missing:
        print(f"Warning: {len(missing)} cited keys missing from .bib.")
        report_lines.append("\n## Missing Citations")
        report_lines.append("The following keys are cited in the .tex file but found no match in the .bib file:")
        
        for key in missing:
            # Fuzzy match
            matches = difflib.get_close_matches(key, available_keys, n=3, cutoff=0.6)
            report_lines.append(f"\n- **{key}**")
            if matches:
                report_lines.append(f"  - *Did you mean?* {', '.join(matches)}")
            else:
                report_lines.append("  - *No similar keys found.*")
    else:
        report_lines.append("\nAll cited keys were found in the bibliography.")

    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    print(f"Alert report saved to {report_path}")

    print(f"Saving to {output_file}...")
    save_bib(db, output_file)
    print("Done.")

if __name__ == "__main__":
    main()
