import os
import fitz  # PyMuPDF
import openai
import csv
from difflib import get_close_matches

# Set your OpenAI API Key
openai.api_key = "your-api-key"

PDF_FOLDER = "ScraperFolder"  # Folder where PDFs are stored
OUTPUT_FILE = "categorized_papers.csv"

CATEGORIES = ["Deep Learning", "Computer Vision", "Reinforcement Learning", "NLP", "Optimization"]

def extract_text_from_pdf(pdf_path):
    """Extracts title and abstract from the PDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""

        # Extract text from the first 2 pages
        for page_num in range(min(2, len(doc))):
            text += doc[page_num].get_text("text") + "\n"

        doc.close()

        # Split lines and remove empty ones
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        title = None
        abstract = None
        collecting_abstract = False
        abstract_lines = []

        for line in lines:
            # Identify the title: First non-empty, meaningful line
            if title is None and line.lower() != "abstract" and not line.isdigit():
                title = line
                continue

            # Identify and collect the abstract text
            if "abstract" in line.lower():
                collecting_abstract = True
                continue  # Skip the word "Abstract"

            if collecting_abstract:
                if len(line.split()) > 5:  # Avoid capturing random short lines
                    abstract_lines.append(line)
                else:
                    break  # Stop collecting if an unrelated section starts

        abstract = " ".join(abstract_lines) if abstract_lines else "No abstract found."

        return title or "Unknown Title", abstract

    except Exception as e:
        print(f"⚠️ Error reading {pdf_path}: {e}")
        return "Unknown Title", "No abstract found."

def categorize_text(title, abstract):
    """Uses GPT API to assign a single category, ensuring it never returns 'Other'."""
    try:
        prompt = f"""
        Title: {title}
        Abstract: {abstract}

        Based on the title and abstract, classify this research paper into exactly one of the following categories:
        {", ".join(CATEGORIES)}.

        Respond only with the most relevant category from the list.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Classify research papers based on predefined categories."},
                      {"role": "user", "content": prompt}]
        )
        category = response["choices"][0]["message"]["content"].strip()

        # Ensure the category is valid, otherwise select the closest match
        if category not in CATEGORIES:
            closest_match = get_close_matches(category, CATEGORIES, n=1, cutoff=0.3)
            return closest_match[0] if closest_match else CATEGORIES[0]  # Default to first category

        return category

    except Exception as e:
        print(f"⚠️ GPT API Error: {e}")
        return CATEGORIES[0]  # Default to first category if API fails

def process_pdfs():
    """Reads PDFs, extracts title/abstract, categorizes them, and stores results in CSV."""
    
    fieldnames = ["Year", "Title", "Abstract", "Category", "File Path"]  # Single category column

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Write column headers

        for year in os.listdir(PDF_FOLDER):
            year_path = os.path.join(PDF_FOLDER, year)
            if os.path.isdir(year_path):
                for pdf_file in os.listdir(year_path):
                    if pdf_file.endswith(".pdf"):
                        pdf_path = os.path.join(year_path, pdf_file)
                        title, abstract = extract_text_from_pdf(pdf_path)

                        if title and abstract:
                            category = categorize_text(title, abstract)

                            # Write data to CSV
                            writer.writerow({
                                "Year": year,
                                "Title": title,
                                "Abstract": abstract,
                                "Category": category,  # Store exactly one category
                                "File Path": pdf_path
                            })

                            print(f"✅ Processed: {title} → Category: {category}")

    print(f"📂 Categorization complete. Data saved in {OUTPUT_FILE}")

if __name__ == "__main__":
    process_pdfs()
