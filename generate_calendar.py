import pandas as pd
import requests
from datetime import timezone
from ics import Calendar, Event

pd.set_option('display.max_rows', None)

OUTPUT_FILENAME = "us_in_high_impact_events.ics"

def fetch_and_filter_events():
    """Fetches events from TradingView for specified countries and filters for high-impact."""
    print("Fetching economic events from TradingView for US & India...")
    url = 'https://economic-calendar.tradingview.com/events'
    today = pd.Timestamp.today().normalize()
    
    headers = {
        'Origin': 'https://in.tradingview.com',
        'Referer': 'https://in.tradingview.com/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }
    
    # --- CHANGE 1: Specify both countries to fetch ---
    countries_to_fetch = ['US', 'IN']
    
    payload = {
        'from': today.isoformat() + 'Z',
        'to': (today + pd.offsets.Day(90)).isoformat() + 'Z',
        'countries': ','.join(countries_to_fetch) # Creates 'US,IN'
    }

    try:
        response = requests.get(url, headers=headers, params=payload)
        response.raise_for_status()
        data = response.json()
        
        if 'result' not in data or not data['result']:
            print("No events found in the API response.")
            return pd.DataFrame()

        df = pd.DataFrame(data['result'])
#        keywords = ['ADP', 'NFP', 'Payroll', 'CPI', 'PPI', 'FOMC', 'Fed', 'Crude', 'Unemployment']

        
        df['importance'] = pd.to_numeric(df['importance'], errors='coerce')
        high_importance_filter = ((df['importance'] == 1) | (df['importance'] == 0))
#        keyword_filter = (df['title'].str.contains('|'.join(keywords), case=False, na=False)) & (df['country'] == 'US')
#        keyword_filter = (
#          (df['country'] == 'US') &
#          (df['title'].str.contains('|'.join(keywords), case=False, na=False)) &
#          (df['importance'] != -1) # <-- This new condition prevents low-importance keyword events
#)
        # Keep rows where importance is 1 (High)
        filtered_df = df[df['importance'] == 1].copy()
        
        filtered_df['date'] = pd.to_datetime(filtered_df['date'])

#        filtered_df = df[high_importance_filter & keyword_filter].copy()

        print(f"Found {len(filtered_df)} total high-impact events for US & India.")
        return filtered_df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()


def create_calendar_from_df(df):
    """Creates an iCalendar object from a DataFrame."""
    c = Calendar()
    
    # --- CHANGE 2: Dictionary to map country codes to flags ---
    country_flags = {
        'US': '🇺🇸',
        'IN': '🇮🇳'
    }
    
    if df.empty:
        return c

    for index, row in df.iterrows():
        e = Event()
        
        # Get the correct flag, with a default globe icon if not found
        flag = country_flags.get(row['country'], '🌐')
        e.name = f"{flag} {row['title']}"
        
        e.begin = row['date']
        e.duration = pd.Timedelta(minutes=30)
        
        description = []
        if pd.notna(row.get('comment')):
            description.append(row['comment'])
        
        e.description = "\n".join(description)
        c.events.add(e)
        
    return c

def main():
    """Main function to run the script."""
    filtered_events_df = fetch_and_filter_events()
    
    if not filtered_events_df.empty:
        print("\n--- High-Impact US & India Events Found ---")
        print(filtered_events_df[['date', 'title', 'country', 'importance']])
        print("-------------------------------------------\n")

        print("Creating calendar file...")
        calendar = create_calendar_from_df(filtered_events_df)
        
        with open(OUTPUT_FILENAME, 'w') as f:
            f.writelines(calendar.serialize_iter())
            
        print(f"✅ Successfully created calendar file: {OUTPUT_FILENAME}")

if __name__ == "__main__":
    main()
