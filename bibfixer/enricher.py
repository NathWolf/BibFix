import requests
import re
from difflib import SequenceMatcher
from unidecode import unidecode

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

def normalize_text(text):
    if not text:
        return ""
    text = unidecode(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()

def normalize_author(author):
    if not author:
        return ""
    author = normalize_text(author)
    author = re.sub(r"[^a-z0-9]", "", author)
    return author

def extract_item_year(item):
    for key in ("issued", "published-print", "published-online"):
        date_parts = item.get(key, {}).get("date-parts", [])
        if date_parts and date_parts[0]:
            return str(date_parts[0][0])
    return ""

def title_similarity(a, b):
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

def normalize_doi(doi):
    if not doi:
        return ""
    doi = doi.strip().lower()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/)", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    return doi

def is_valid_doi(doi):
    doi = normalize_doi(doi)
    if not doi:
        return False
    return re.match(r"^10\.\d{4,9}/\S+$", doi) is not None

def normalize_container(item):
    container = item.get("container-title", [""])
    if container:
        return normalize_text(container[0])
    return ""

def normalize_pages(pages):
    if not pages:
        return ""
    return re.sub(r"[^0-9\-]", "", pages)

def item_fields_match(entry, item):
    entry_journal = normalize_text(entry.get("journal", "")) or normalize_text(entry.get("booktitle", ""))
    item_journal = normalize_container(item)
    if entry_journal and item_journal and entry_journal != item_journal:
        return False, "journal mismatch"

    entry_volume = normalize_text(entry.get("volume", ""))
    item_volume = normalize_text(item.get("volume", ""))
    if entry_volume and item_volume and entry_volume != item_volume:
        return False, "volume mismatch"

    entry_issue = normalize_text(entry.get("number", ""))
    item_issue = normalize_text(item.get("issue", ""))
    if entry_issue and item_issue and entry_issue != item_issue:
        return False, "issue mismatch"

    entry_pages = normalize_pages(entry.get("pages", ""))
    item_pages = normalize_pages(item.get("page", ""))
    if entry_pages and item_pages and entry_pages != item_pages:
        return False, "pages mismatch"

    return True, ""

def item_has_author_match(item, authors):
    if not authors:
        return True
    item_authors = item.get("author", [])
    if not item_authors:
        return True
    normalized_authors = {normalize_author(a) for a in authors if a}
    for author in item_authors:
        family = normalize_author(author.get("family", ""))
        if family and family in normalized_authors:
            return True
    return False

def search_doi(title, authors, year, entry=None, verify_log=None, entry_id=None):
    """
    Search for a DOI using Crossref API.
    Args:
        title (str): Title of the paper.
        authors (list[str]): Author last names.
        year (str): Year of publication.
    """
    # https://github.com/CrossRef/rest-api-doc
    # Using the /works endpoint with query parameters
    
    if not title:
        return None

    # Clean title for search
    clean_title = unidecode(title).replace('{', '').replace('}', '')
    
    url = "https://api.crossref.org/works"
    params = {
        "query.title": clean_title,
        "rows": 5,
    }
    if authors:
        params["query.author"] = unidecode(authors[0])
        
    headers = {
        'User-Agent': 'BibFixer/1.0 (mailto:agent@example.com)' 
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get('message', {}).get('items', [])
            if items:
                best_match = None
                best_score = 0.0
                for item in items:
                    found_title = item.get("title", [""])[0]
                    score = title_similarity(title, found_title)
                    if score < 0.85:
                        if verify_log is not None and entry_id:
                            verify_log.append(f"- {entry_id}: reject title similarity {score:.2f} ({found_title[:80]}...)")
                        continue
                    if not item_has_author_match(item, authors):
                        if verify_log is not None and entry_id:
                            verify_log.append(f"- {entry_id}: reject author mismatch ({found_title[:80]}...)")
                        continue
                    item_year = extract_item_year(item)
                    if year and item_year and year != item_year:
                        if verify_log is not None and entry_id:
                            verify_log.append(f"- {entry_id}: reject year mismatch ({year} vs {item_year})")
                        continue
                    if entry is not None:
                        fields_match, reason = item_fields_match(entry, item)
                        if not fields_match:
                            if verify_log is not None and entry_id:
                                verify_log.append(f"- {entry_id}: reject {reason} ({found_title[:80]}...)")
                            continue
                    if score > best_score:
                        best_score = score
                        best_match = item
                if best_match:
                    doi = best_match.get("DOI")
                    if doi and is_valid_doi(doi):
                        if verify_log is not None and entry_id:
                            verify_log.append(f"- {entry_id}: accept DOI {normalize_doi(doi)} (score {best_score:.2f})")
                        return normalize_doi(doi)
                    if verify_log is not None and entry_id:
                        verify_log.append(f"- {entry_id}: reject invalid DOI format ({doi})")
                # else:
                #     print(f"Rejected match: '{title}' vs '{found_title}' (Ratio: {ratio:.2f})")
    except Exception as e:
        # print(f"Error fetching DOI for {title}: {e}")
        pass
        
    return None

def enrich_database(database, pbar=None, verify=False):
    """
    Iterate over the database and find missing DOIs.
    """
    items_modified = []
    verify_log = []
    total = len(database.entries)
    
    iterator = database.entries
    if pbar:
        iterator = pbar(database.entries, desc="Enriching DOIs")
        
    for entry in iterator:
        if "doi" not in entry or not entry["doi"].strip():
            # Try to find DOI
            title = entry.get('title', '')
            authors = get_authors_list(entry)
            year_raw = entry.get("year", "")
            year_match = re.search(r"\d{4}", year_raw)
            year = year_match.group(0) if year_match else ""
            
            # Rate limiting / politeness sleep if needed (Crossref is generous but good practice)
            # time.sleep(0.1) 
            
            found_doi = search_doi(
                title,
                authors,
                year,
                entry=entry,
                verify_log=verify_log if verify else None,
                entry_id=entry.get("ID", ""),
            )
            if found_doi:
                # Store old value just in case? already checked it was empty.
                entry['doi'] = found_doi
                # Record the change: (ID, added_doi)
                items_modified.append((entry['ID'], found_doi))
                
    return database, items_modified, verify_log
