import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import time
import pandas as pd

REQUEST_TIMEOUT_SECONDS = 10
REQUEST_DELAY_SECONDS = 2
RIGHTMOVE_PAGE_SIZE = 24
LISTING_COLUMNS = [
    'Address',
    'City',
    'Postcode',
    'Price',
    'Rooms',
    'Link',
    'DateLastUpdated',
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def build_rightmove_url(filters: dict[str, str], channel: str = 'BUY') -> str:
    channel = channel.upper()
    action = 'sale' if channel == 'BUY' else 'rent'
    preposition = 'for' if channel == 'BUY' else 'to'
    return f'https://www.rightmove.co.uk/property-{preposition}-{action}/find.html' + '?' + urlencode(filters)

def empty_listings_df():
    return pd.DataFrame(columns=LISTING_COLUMNS)

def get_total_results(url, session=None):
    session = session or requests.Session()
    response = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    results_elem = soup.select_one('[class^="ResultsCount_resultsCount"] > p > span')
    if results_elem:
        try:
            total_results = int(results_elem.text.strip().replace(',', ''))
            print(f"Total results found: {total_results}")
            return total_results
        except ValueError:
            print("Could not parse total results number")
    return None

def parse_listing_cards(html, filters):
    soup = BeautifulSoup(html, 'html.parser')
    result_cards = soup.select('[class$="propertyCard-details"]')
    listings = []

    for card in result_cards:
        try:
            address_el = card.select_one('div[class^="PropertyAddress_address"]')
            price_el = card.select_one('div[class^="PropertyPrice_price"]')
            roomCount_el = card.select_one('span[class^="PropertyInformation_bedroomsCount"]')
            link_elem = card.select_one('a[data-testid="property-details-lozenge"]')
            date_el = card.select_one('span[class^="MarketedBy_addedOrReduced"]')

            address = address_el.text.strip() if address_el else None
            price = price_el.text.strip() if price_el else None
            room_count = roomCount_el.text.strip() if roomCount_el else None
            relative_link = link_elem['href'] if link_elem and link_elem.has_attr('href') else None
            date_text = date_el.text.strip() if date_el else None

            listings.append({
                'Address': address,
                'City': filters.get('city'),
                'Postcode': filters.get('searchLocation'),
                'Price': price,
                'Rooms': room_count,
                'Link': relative_link,
                'DateLastUpdated': date_text
            })
        except Exception as exc:
            print(f"Failed to parse listing card: {exc}")
            continue

    return listings

def scrape_listings(filters, max_pages, channel):
    if max_pages <= 0:
        print("max_pages must be greater than 0")
        return empty_listings_df()

    session = requests.Session()
    session.headers.update(HEADERS)

    base_filters = filters.copy()
    url = build_rightmove_url(base_filters, channel=channel)
    total_results = get_total_results(url, session=session)
    if total_results is None or total_results == 0:
        print("No results found")
        return empty_listings_df()

    pages = (total_results + RIGHTMOVE_PAGE_SIZE - 1) // RIGHTMOVE_PAGE_SIZE
    pages_to_scrape = min(pages, max_pages)

    listings = []
    for page_num in range(pages_to_scrape):
        page_filters = base_filters.copy()
        page_filters['index'] = page_num * RIGHTMOVE_PAGE_SIZE
        url = build_rightmove_url(page_filters, channel=channel)
        response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        page_listings = parse_listing_cards(response.text, page_filters)
        if not page_listings:
            print(f"No results on page {page_num + 1}")
            break

        listings.extend(page_listings)

        time.sleep(REQUEST_DELAY_SECONDS)
    return pd.DataFrame(listings, columns=LISTING_COLUMNS)
