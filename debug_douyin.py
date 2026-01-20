try:
    print("Importing douyin_api...")
    from douyin_api import DouyinDownloader
    print("DouyinDownloader imported successfully.")
    
    print("Initializing...")
    dd = DouyinDownloader(headless=True)
    
    test_url = "https://www.douyin.com/video/7331535497275624738" # Random sample
    print(f"Testing URL: {test_url}")
    
    # Just check if it crashes on init, we might not get 200 OK on random URL but that's fine
    # We mainly want to see if Playwright launches without error
    print("Running get_video_info (might fail on network, but should not crash on import)...")
    # We don't actually wait for the full result to avoid long delays, just start it.
    # Actually let's try a dry run.
    
    info, err = dd.get_video_info(test_url)
    if info:
        print(f"Success! Title: {info.get('title')}")
    else:
        print(f"Failed (Expected if URL invalid): {err}")
        
    print("Verification complete.")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
