import argparse
from .core import fix_bibliography

def main():
    parser = argparse.ArgumentParser(description="Fix and enrich bibliography files.")
    parser.add_argument('input_file', help="Path to input .bib file")
    parser.add_argument('-o', '--output', help="Path to output .bib file", default=None)
    parser.add_argument('--verify', action='store_true', help="Emit DOI verification details")
    
    args = parser.parse_args()
    
    fix_bibliography(args.input_file, args.output, verify=args.verify)

if __name__ == "__main__":
    main()
