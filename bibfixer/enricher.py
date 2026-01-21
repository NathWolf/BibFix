import requests
import re
from unidecode import unidecode
import urllib.parse
import time

def get_authors_list(entry):
    """
    Get a list of authors from a bib entry. 
    Simplistic parsing of the 'author' field.
    """
    author_str = entry.get('author', '')
    if not author_str:
        author_str = entry.get('editor', '')
    
    # Split by ' and ' which is standard bibtex
    authors = author_str.split(' and ')
    # Clean up last names
    last_names = []
    for auth in authors:
        # If "Last, First", take First
        parts = auth.split(',')
        if len(parts) > 0:
            last_names.append(parts[0].strip())
        else:
            last_names.append(auth.strip())
    return last_names

def search_doi(title, author):
    """
    Search for a DOI using Crossref API.
    Args:
        title (str): Title of the paper.
        author (str): First author's last name.
    """
    # https://github.com/CrossRef/rest-api-doc
    # Using the /works endpoint with query parameters
    
    if not title:
        return None

    # Clean title for search
    clean_title = unidecode(title).replace('{', '').replace('}', '')
    
    url = "https://api.crossref.org/works"
    params = {
        'query.title': clean_title,
        'rows': 1,
    }
    if author:
        params['query.author'] = unidecode(author)
        
    headers = {
        'User-Agent': 'BibFixer/1.0 (mailto:agent@example.com)' 
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get('message', {}).get('items', [])
            if items:
                # Check if the title matches reasonably well?
                # For now, just take the top hit if it exists.
                # In a real tool, we might want to fuzzy match titles to be sure.
                return items[0].get('DOI')
    except Exception as e:
        # print(f"Error fetching DOI for {title}: {e}")
        pass
        
    return None

def enrich_database(database, pbar=None):
    """
    Iterate over the database and find missing DOIs.
    """
    items_modified = 0
    total = len(database.entries)
    
    iterator = database.entries
    if pbar:
        iterator = pbar(database.entries, desc="Enriching DOIs")
        
    for entry in iterator:
        if 'doi' not in entry or not entry['doi'].strip():
            # Try to find DOI
            title = entry.get('title', '')
            authors = get_authors_list(entry)
            first_author = authors[0] if authors else ''
            
            # Rate limiting / politeness sleep if needed (Crossref is generous but good practice)
            # time.sleep(0.1) 
            
            found_doi = search_doi(title, first_author)
            if found_doi:
                entry['doi'] = found_doi
                items_modified += 1
                
    return database, items_modified
