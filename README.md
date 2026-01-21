# DOI Filler & Bibliography Fixer

A simple tool to help you clean up your BibTeX files and automatically find missing DOIs for your articles. 

## Features

- **Standardizes** your bibliography entries.
- **Deduplicates** entries (merges duplicates, renames colliding IDs).
- **Enriches** your bibliography by automatically finding missing DOIs from CrossRef.
- **Non-destructive**: Creates a new file by default (e.g., `myfile_fix.bib`), keeping your original safe.

## Installation

1. **Clone or Download** this folder.
2. **Install dependencies**. You need Python installed. Then run:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

It's super easy to use!

1. Open your terminal.
2. Navigate to this folder.
3. Run the script on your bibliography file:

   ```bash
   python fix_bib.py path/to/your/bibliography.bib
   ```

   **Example:**
   If your file is named `articles.bib`:
   ```bash
   python fix_bib.py articles.bib
   ```

4. The tool will think for a bit (finding DOIs takes a few seconds per article) and then create a new file named `articles_fix.bib` in the same folder.

## What it does

- It reads your `.bib` file.
- It fixes common formatting issues.
- It searches for missing DOIs online.
- It saves a **new** clean file.

## For Students / Tips

- **Always check the output!** Automations differ from humans.
- If the tool cannot find a DOI, it might be because the title is very generic or the service is temporarily unavailable.
- This tool respects your existing DOIs; if you already have one, it won't overwrite it.
