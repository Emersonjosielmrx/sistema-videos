import json
import os
from playwright.sync_api import sync_playwright

def test_drive_login(cookie_file):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Load state
        context = browser.new_context(storage_state=cookie_file)
        page = context.new_page()
        
        # Navigate to Google Drive
        page.goto("https://drive.google.com/drive/my-drive")
        page.wait_for_timeout(3000)
        
        # Check if we are logged in by seeing if the 'New' or 'Novo' button exists
        # Google Drive UI might have a specific aria label for the 'New' button
        # Try to find the user profile image or generic elements that indicate login
        
        is_logged_in = False
        try:
            # Check for the Google Account avatar (usually in banner)
            avatar = page.query_selector('a[aria-label*="Google"]')
            if avatar:
                is_logged_in = True
                print(f"Logged in successfully. Aria-label: {avatar.get_attribute('aria-label')}")
        except Exception as e:
            print(f"Error checking avatar: {e}")
            
        print(f"Status for {cookie_file}: {'LOGGED IN' if is_logged_in else 'NOT LOGGED IN'}")
        
        browser.close()

if __name__ == "__main__":
    test_drive_login("D:/logins-google/sessions/canalalucinaai.json")
