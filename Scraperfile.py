import os
import requests
from bs4 import BeautifulSoup
import threading

BASE_URL = "https://proceedings.neurips.cc"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_years():
    """Fetch all available years and their URLs."""
    response = requests.get(BASE_URL, headers=HEADERS)
    if response.status_code != 200:
        print("❌ Error fetching the main page")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    years = {}
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith("/paper_files/paper") and href.split("/")[-1].isdigit():
            year = int(href.split("/")[-1])
            years[year] = BASE_URL + href

    return years

def fetch_papers(year_url):
    """Fetch paper URLs for a given year."""
    response = requests.get(year_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to fetch papers for {year_url}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    paper_links = []

    for link in soup.find_all('a', href=True):
        if "Abstract" in link['href']:
            paper_links.append(BASE_URL + link['href'])

    return paper_links

def download_paper(paper_url, year_folder):
    """Download a single paper PDF."""
    try:
        response = requests.get(paper_url, headers=HEADERS)
        if response.status_code != 200:
            print(f"❌ Failed to access paper page: {paper_url}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        pdf_link = soup.find('a', href=True, text="Paper")

        if not pdf_link:
            print(f"⚠️ No PDF found for: {paper_url}")
            return

        pdf_url = BASE_URL + pdf_link['href']
        paper_title = soup.title.text.strip().replace(" ", "_").replace("/", "-")
        file_path = os.path.join(year_folder, f"{paper_title}.pdf")

        pdf_response = requests.get(pdf_url, headers=HEADERS, stream=True)
        if pdf_response.status_code != 200:
            print(f"❌ Failed to download: {pdf_url}")
            return

        with open(file_path, "wb") as file:
            for chunk in pdf_response.iter_content(1024):
                file.write(chunk)
        
        print(f"📥 Downloaded: {file_path}")
    
    except Exception as e:
        print(f"⚠️ Error downloading {paper_url}: {e}")

def main():
    print("🔍 Fetching available years...")
    years = fetch_years()
    if not years:
        print("❌ No years found. Exiting...")
        return

    print("\n✅ Available Years:", sorted(years.keys(), reverse=True))
    user_input = input("Enter a year or range (e.g., 2021 or 2015-2018): ").strip()

    selected_years = []

    if "-" in user_input:  # Range input
        try:
            start, end = map(int, user_input.split("-"))
            if start > end:
                print("❌ Invalid range. Start year must be less than or equal to end year.")
                return
            selected_years = [year for year in range(start, end + 1) if year in years]
        except ValueError:
            print("❌ Invalid format. Please enter a valid range (e.g., 2015-2018).")
            return
    else:  # Single year input
        try:
            selected_year = int(user_input)
            if selected_year in years:
                selected_years = [selected_year]
            else:
                print("❌ Year not found. Please enter a valid year.")
                return
        except ValueError:
            print("❌ Invalid input. Please enter a valid year or range.")
            return

    if not selected_years:
        print("❌ No valid years selected.")
        return

    for year in selected_years:
        year_folder = os.path.join("ScraperFolder", str(year))
        os.makedirs(year_folder, exist_ok=True)
        
        print(f"\n📂 Fetching papers for {year}...")
        papers = fetch_papers(years[year])

        print(f"📊 Found {len(papers)} papers for {year}")

        threads = []
        for paper_url in papers:
            thread = threading.Thread(target=download_paper, args=(paper_url, year_folder))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    print("✅ All downloads completed!")

if __name__ == "__main__":
    main()
