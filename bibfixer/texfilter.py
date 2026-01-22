import re

def strip_tex_comments(text):
    lines = []
    for line in text.splitlines():
        cleaned = []
        i = 0
        while i < len(line):
            char = line[i]
            if char == "%" and (i == 0 or line[i - 1] != "\\"):
                break
            cleaned.append(char)
            i += 1
        lines.append("".join(cleaned))
    return "\n".join(lines)

def extract_citation_keys(tex_path):
    """
    Extract citation keys from a .tex file.
    Returns (keys, include_all).
    """
    with open(tex_path, "r", encoding="utf-8") as f:
        text = f.read()

    text = strip_tex_comments(text)

    cite_re = re.compile(
        r"\\cite[a-zA-Z*]*\s*(\[[^\]]*\]\s*){0,2}\{([^}]*)\}",
        re.DOTALL,
    )
    nocite_re = re.compile(
        r"\\nocite\s*(\[[^\]]*\]\s*){0,2}\{([^}]*)\}",
        re.DOTALL,
    )

    include_all = False
    keys = set()

    for match in nocite_re.finditer(text):
        raw = match.group(2)
        for key in raw.split(","):
            cleaned = key.strip()
            if cleaned == "*":
                include_all = True
            elif cleaned:
                keys.add(cleaned)

    for match in cite_re.finditer(text):
        raw = match.group(2)
        for key in raw.split(","):
            cleaned = key.strip()
            if cleaned:
                keys.add(cleaned)

    return keys, include_all

def filter_database_by_keys(database, keys, include_all=False):
    """
    Filter bibliography entries by citation keys.
    Returns (database, missing_keys).
    """
    if include_all:
        return database, []

    keys_set = set(keys)
    if not keys_set:
        database.entries = []
        return database, []

    existing_keys = {entry["ID"] for entry in database.entries}
    missing = sorted(keys_set - existing_keys)
    database.entries = [entry for entry in database.entries if entry["ID"] in keys_set]
    return database, missing
