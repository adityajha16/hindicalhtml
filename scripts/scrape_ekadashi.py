#!/usr/bin/env python3
"""
Ekadashi Scraper - Drik Panchang
Scrapes Ekadashi dates for a given year from Drik Panchang
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import re
from datetime import datetime

def setup_driver():
    """Set up headless Chromium driver"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.binary_location = '/snap/chromium/current/usr/lib/chromium-browser/chrome'
    
    from selenium.webdriver.chrome.service import Service
    service = Service('/snap/chromium/current/usr/lib/chromium-browser/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_ekadashi_dates(year=2026):
    """Scrape Ekadashi dates from Drik Panchang"""
    
    driver = setup_driver()
    ekadashi_data = []
    
    try:
        # Drik Panchang Ekadashi page
        url = f"https://www.drikpanchang.com/vrat/ekadashi/ekadashi-vrat-list.html?year={year}"
        print(f"Fetching: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Find all Ekadashi entries
        # Drik Panchang usually lists them in a table or list format
        try:
            # Try to find the main content area
            content = driver.find_element(By.CSS_SELECTOR, '.dpTableNormal, .dpTable, table')
            rows = content.find_elements(By.TAG_NAME, 'tr')
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if len(cells) >= 2:
                        name = cells[0].text.strip()
                        date_text = cells[1].text.strip() if len(cells) > 1 else ''
                        
                        if 'ekadashi' in name.lower():
                            ekadashi_data.append({
                                'name': name,
                                'date_text': date_text,
                                'raw': row.text
                            })
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Table method failed: {e}")
            
            # Fallback: try to get all text and parse
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            print("Page text (first 2000 chars):")
            print(page_text[:2000])
            
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        driver.quit()
    
    return ekadashi_data

def scrape_individual_ekadashi(year=2026):
    """Alternative: scrape each Ekadashi page individually"""
    
    ekadashi_names = [
        "pausha-putrada", "sat-tila", "jaya", "vijaya", "amalaki",
        "papmochani", "kamada", "varuthini", "mohini", "apara",
        "nirjala", "yogini", "devshayani", "kamika", "shravana-putrada",
        "aja", "parsva", "indira", "papankusha", "rama",
        "devutthana", "utpanna", "mokshada", "saphala"
    ]
    
    driver = setup_driver()
    results = []
    
    try:
        for name in ekadashi_names:
            url = f"https://www.drikpanchang.com/vrat/ekadashi/{name}-ekadashi-vrat-date.html?year={year}"
            print(f"Fetching: {name}...")
            
            try:
                driver.get(url)
                time.sleep(3)
                
                # Try to extract date from the page
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                
                # Look for date patterns like "January 15, 2026"
                date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
                dates_found = re.findall(date_pattern, page_text)
                
                results.append({
                    'name': name.replace('-', ' ').title() + ' Ekadashi',
                    'url': url,
                    'dates_found': dates_found[:3] if dates_found else [],
                    'page_snippet': page_text[:500]
                })
                
            except Exception as e:
                print(f"Error fetching {name}: {e}")
                
    finally:
        driver.quit()
    
    return results

if __name__ == "__main__":
    import sys
    
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    
    print(f"\n=== Scraping Ekadashi dates for {year} ===\n")
    
    # Try main list page first
    data = scrape_ekadashi_dates(year)
    
    if data:
        print(f"\nFound {len(data)} Ekadashi entries:")
        for item in data:
            print(json.dumps(item, indent=2))
    else:
        print("\nMain list didn't work. Trying individual pages...")
        data = scrape_individual_ekadashi(year)
        
        print(f"\nResults from individual pages:")
        for item in data:
            print(f"\n{item['name']}:")
            print(f"  Dates found: {item['dates_found']}")
    
    # Save results
    with open(f'/var/www/hindicalendar/data/ekadashi_{year}_raw.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nRaw data saved to /var/www/hindicalendar/data/ekadashi_{year}_raw.json")
