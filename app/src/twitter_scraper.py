import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright

# Zugangsdaten aus Umgebungsvariablen holen
USERNAME = os.getenv("X_USERNAME")
PASSWORD = os.getenv("X_PASSWORD")

def login_to_x(page):
    print("🔐 Starte Login-Prozess...")
    page.goto("https://x.com/login")
    page.wait_for_timeout(4000)

    page.locator('input[name="text"]').fill(USERNAME)
    page.locator('div[role="button"]').nth(1).click()
    page.wait_for_timeout(3000)

    page.locator('input[name="password"]').fill(PASSWORD)
    page.locator('div[role="button"]').nth(1).click()
    page.wait_for_timeout(5000)
    print("✅ Login abgeschlossen!")

def scrape_tweets(keyword="Klima", max_tweets=20):
    print(f"🔍 Suche nach Tweets zu: '{keyword}' (max. {max_tweets} Tweets)")

    tweets_data = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)  # Firefox statt Chromium
        context = browser.new_context()
        page = context.new_page()

        login_to_x(page)

        search_url = f"https://x.com/search?q={keyword}%20lang%3Ade&f=live"
        print(f"🌐 Öffne Seite: {search_url}")
        page.goto(search_url)
        time.sleep(5)

        scroll_count = 0
        while len(tweets_data) < max_tweets:
            tweet_elements = page.query_selector_all("article")
            print(f"🔎 Gefundene Tweet-Elemente: {len(tweet_elements)}")

            new_tweets = 0

            for tweet in tweet_elements:
                try:
                    content = tweet.inner_text()
                    lines = content.split('\n')
                    username = lines[0] if lines else ""
                    text = '\n'.join(lines[2:-4]) if len(lines) > 6 else content
                    timestamp = tweet.query_selector('time').get_attribute('datetime') if tweet.query_selector('time') else ''
                    tweet_url = tweet.query_selector('a:has(time)').get_attribute('href') if tweet.query_selector('a:has(time)') else ''
                    full_url = f"https://x.com{tweet_url}" if tweet_url else ''

                    if any(d['url'] == full_url for d in tweets_data):
                        continue

                    tweets_data.append({
                        "username": username,
                        "text": text,
                        "timestamp": timestamp,
                        "url": full_url
                    })
                    new_tweets += 1
                    print(f"➕ Neuer Tweet ({len(tweets_data)}/{max_tweets})")

                    if len(tweets_data) >= max_tweets:
                        break
                except Exception as e:
                    print(f"⚠️ Fehler beim Verarbeiten eines Tweets: {e}")
                    continue

            if new_tweets == 0:
                print("⏸️ Keine neuen Tweets – beende Scrollen.")
                break

            page.mouse.wheel(0, 2000)
            scroll_count += 1
            print(f"⬇️ Scrolle weiter... (#{scroll_count})")
            time.sleep(2)

        browser.close()
        print("🧹 Browser geschlossen.")

    return tweets_data

# Ausführung & Speicherung
data = scrape_tweets("Klima", max_tweets=30)
df = pd.DataFrame(data)
df.to_csv("tweets_playwright_firefox_scrape.csv", index=False, encoding="utf-8")
print(f"✅ {len(df)} Tweets gespeichert in 'tweets_playwright_firefox_scrape.csv'")
import os
import time
import pandas as pd
from playwright.sync_api import sync_playwright

# Zugangsdaten aus Umgebungsvariablen holen
USERNAME = os.getenv("X_USERNAME")
PASSWORD = os.getenv("X_PASSWORD")

def login_to_x(page):
    print("🔐 Starte Login-Prozess...")
    page.goto("https://x.com/login")
    page.wait_for_timeout(4000)

    page.locator('input[name="text"]').fill(USERNAME)
    page.locator('div[role="button"]').nth(1).click()
    page.wait_for_timeout(3000)

    page.locator('input[name="password"]').fill(PASSWORD)
    page.locator('div[role="button"]').nth(1).click()
    page.wait_for_timeout(5000)
    print("✅ Login abgeschlossen!")

def scrape_tweets(keyword="Klima", max_tweets=20):
    print(f"🔍 Suche nach Tweets zu: '{keyword}' (max. {max_tweets} Tweets)")

    tweets_data = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)  # Firefox statt Chromium
        context = browser.new_context()
        page = context.new_page()

        login_to_x(page)

        search_url = f"https://x.com/search?q={keyword}%20lang%3Ade&f=live"
        print(f"🌐 Öffne Seite: {search_url}")
        page.goto(search_url)
        time.sleep(5)

        scroll_count = 0
        while len(tweets_data) < max_tweets:
            tweet_elements = page.query_selector_all("article")
            print(f"🔎 Gefundene Tweet-Elemente: {len(tweet_elements)}")

            new_tweets = 0

            for tweet in tweet_elements:
                try:
                    content = tweet.inner_text()
                    lines = content.split('\n')
                    username = lines[0] if lines else ""
                    text = '\n'.join(lines[2:-4]) if len(lines) > 6 else content
                    timestamp = tweet.query_selector('time').get_attribute('datetime') if tweet.query_selector('time') else ''
                    tweet_url = tweet.query_selector('a:has(time)').get_attribute('href') if tweet.query_selector('a:has(time)') else ''
                    full_url = f"https://x.com{tweet_url}" if tweet_url else ''

                    if any(d['url'] == full_url for d in tweets_data):
                        continue

                    tweets_data.append({
                        "username": username,
                        "text": text,
                        "timestamp": timestamp,
                        "url": full_url
                    })
                    new_tweets += 1
                    print(f"➕ Neuer Tweet ({len(tweets_data)}/{max_tweets})")

                    if len(tweets_data) >= max_tweets:
                        break
                except Exception as e:
                    print(f"⚠️ Fehler beim Verarbeiten eines Tweets: {e}")
                    continue

            if new_tweets == 0:
                print("⏸️ Keine neuen Tweets – beende Scrollen.")
                break

            page.mouse.wheel(0, 2000)
            scroll_count += 1
            print(f"⬇️ Scrolle weiter... (#{scroll_count})")
            time.sleep(2)

        browser.close()
        print("🧹 Browser geschlossen.")

    return tweets_data

# Ausführung & Speicherung
data = scrape_tweets("Klima", max_tweets=30)
df = pd.DataFrame(data)
df.to_csv("tweets_playwright_firefox_scrape.csv", index=False, encoding="utf-8")
print(f"✅ {len(df)} Tweets gespeichert in 'tweets_playwright_firefox_scrape.csv'")
