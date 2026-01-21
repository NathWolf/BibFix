import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
import os

def load_bib(path):
    """
    Load a bibliography file.
    
    Args:
        path (str): Path to the .bib file.
        
    Returns:
        bibtexparser.bibdatabase.BibDatabase: The parsed bibliography database.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
        
    with open(path, 'r', encoding='utf-8') as bibfile:
        parser = BibTexParser(common_strings=True)
        parser.ignore_nonstandard_types = False
        parser.homogenise_fields = False  # Keep original fields as much as possible
        bib_database = bibtexparser.load(bibfile, parser=parser)
        
    return bib_database

def save_bib(database, path):
    """
    Save a bibliography database to a file.
    
    Args:
        database (bibtexparser.bibdatabase.BibDatabase): The bibliography database.
        path (str): Path to save the .bib file.
    """
    writer = BibTexWriter()
    writer.indent = '  ' # 2 spaces indent
    with open(path, 'w', encoding='utf-8') as bibfile:
        bibfile.write(writer.write(database))
