import requests
import json
import re

def get_dailymotion_info(url):
    print(f"Testing URL: {url}")
    # Extract ID
    # Patterns: /video/xID, /embed/video/xID
    video_id = None
    match = re.search(r'video/([a-z0-9]+)', url)
    if match:
        video_id = match.group(1)
    
    if not video_id:
        print("Could not extract Video ID")
        return

    print(f"Video ID: {video_id}")
    
    # API Endpoint
    api_url = f"https://www.dailymotion.com/player/metadata/video/{video_id}"
    print(f"Fetching API: {api_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.dailymotion.com/'
        }
        res = requests.get(api_url, headers=headers, timeout=10)
        print(f"Status Code: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            # print(json.dumps(data, indent=2))
            
            # Look for qualities
            qualities = data.get('qualities', {})
            print(f"Qualities found: {list(qualities.keys())}")
            
            # Usually 'auto' has the master m3u8
            if 'auto' in qualities:
                m3u8_url = qualities['auto'][0].get('url')
                print(f"Master M3U8: {m3u8_url}")
                
                # Verify access
                r2 = requests.head(m3u8_url)
                print(f"M3U8 Access: {r2.status_code}")
            else:
                print("No 'auto' quality found. Checking others...")
                for q, items in qualities.items():
                    print(f"{q}: {items[0].get('url')}")
                    
        else:
            print("API Request failed")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with the user's ID from previous context if available, or a generic one.
    # User mentioned 'x9y5x54' in previous logs.
    get_dailymotion_info("https://www.dailymotion.com/video/x9y5x54")
