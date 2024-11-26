import requests
import json
import time
from linkedin_api import Linkedin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv
import concurrent.futures
import re
import sys


name_var = "Name"
srch_var = "Key search var"
def google_search_script():
    global alpha
    # Konfigurationsvariablen
    API_KEY = ''          # Ersetze mit deinem neuen API-Schlüssel
    SEARCH_ENGINE_ID = ''       # Deine Suchmaschinen-ID
    QUERY = f'"{name_var}""{srch_var}"'      # Angepasste Suchanfrage
    NUM_RESULTS = 10                              # Anzahl der gewünschten Ergebnisse (max 100)

    def google_search(query, api_key, cse_id, start=1):
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'q': query,
            'key': api_key,
            'cx': cse_id,
            'start': start,
            'num': 10,                        # Maximale Anzahl pro Anfrage (1-10)
        }
        print(f"[Google] Anfrage an Google API senden: Start={start}")
        response = requests.get(url, params=params)
        print(f"[Google] HTTP-Statuscode: {response.status_code}")
        if response.status_code != 200:
            print(f"[Google] Fehlerhafte Antwort: {response.text}")
        response.raise_for_status()
        return response.json()

    def main_google():
        global alpha
        results = []
        start = 1
        while start <= NUM_RESULTS:
            try:
                data = google_search(QUERY, API_KEY, SEARCH_ENGINE_ID, start)
                items = data.get('items', [])
                if not items:
                    print("[Google] Keine weiteren Ergebnisse gefunden.")
                    break
                for item in items:
                    results.append({
                        'title': item.get('title'),
                        'link': item.get('link'),
                        'snippet': item.get('snippet')
                    })
                print(f"[Google] Erhaltene Ergebnisse: {len(items)}")
                start += 10
                time.sleep(1)  # Vermeide Überschreiten der Rate Limits
            except Exception as e:
                print(f"[Google] Fehler bei der Suche: {e}")
                break

        # Ergebnisse anzeigen oder speichern
        if results:
            alpha = "Found:"
            print("\n[Google] Suchergebnisse:")
            for idx, result in enumerate(results, start=1):
                print(f"{idx}. {result['title']}\n{result['link']}\n{result['snippet']}\n")
                alpha += (f"{idx}. {result['title']}\n{result['link']}\n{result['snippet']}\n")
        else:
            print("[Google] Keine Ergebnisse gefunden.")

    main_google()

def linkedin_search_script():
    global beta
    # Authentifizierung
    linkedin_email = ''
    linkedin_password = ''
    
    try:
        print("\n[LinkedIn] Authentifiziere bei LinkedIn...")
        api = Linkedin(linkedin_email, linkedin_password)
        print("[LinkedIn] Authentifizierung erfolgreich.\n")
    except Exception as e:
        print(f"[LinkedIn] Fehler bei der Authentifizierung: {e}")
        return

    # Suchparameter
    name_to_search = name_var
    search_term = srch_var

    print(f"[LinkedIn] Suche nach Personen mit dem Namen: {name_to_search} und dem Suchbegriff: {search_term}\n")
    search_results = api.search_people(keywords=name_to_search)

    if not search_results:
        print("[LinkedIn] Keine Suchergebnisse gefunden.")
    else:
        print(f"[LinkedIn] Anzahl gefundener Personen: {len(search_results)}\n")

    # Iteriere durch die Suchergebnisse
    for idx, person in enumerate(search_results, start=1):
        urn_id = person.get('urn_id')
        print(f"[LinkedIn] Verarbeite Ergebnis {idx}: Public ID = {urn_id}")

        if not urn_id:
            print("[LinkedIn] Keine urn_id gefunden, überspringe...\n")
            continue

        try:
            # Profildaten abrufen
            profile = api.get_profile(urn_id)
            first_name = profile.get('firstName', '')
            last_name = profile.get('lastName', '')
            print(f"[LinkedIn] Profil abgerufen: {first_name} {last_name}")
        except Exception as e:
            print(f"[LinkedIn] Fehler beim Abrufen des Profils: {e}\n")
            continue

        # Überprüfen, ob der Suchbegriff in der Zusammenfassung vorhanden ist
        summary = profile.get('summary', '').lower()
        summary_contains = search_term.lower() in summary

        # Überprüfen, ob der Suchbegriff in den Arbeitserfahrungen vorhanden ist
        experiences = profile.get('experience', [])
        experiences_contains = False

        print("\n[LinkedIn] Arbeitserfahrungen:")
        if not experiences:
            print("  Keine Arbeitserfahrungen gefunden.")
        else:
            for exp_idx, experience in enumerate(experiences, start=1):
                title = experience.get('title', 'Keine Titelangabe').lower()
                company = experience.get('companyName', '').lower()
                description = experience.get('description', '').lower()
                
                # Überprüfe, ob der Suchbegriff in Titel, Firma oder Beschreibung vorkommt
                if (search_term.lower() in title or
                    search_term.lower() in company or
                    search_term.lower() in description):
                    experiences_contains = True

        if summary_contains or experiences_contains:
            beta = "Found:"
            print(f"**Gefunden:** {first_name} {last_name}")
            print(f"Profil URL: https://www.linkedin.com/in/{urn_id}/\n")
            beta += (f"**Gefunden:** {first_name} {last_name}")
            beta += (f"Profil URL: https://www.linkedin.com/in/{urn_id}/\n") 
        else:
            print(f"[LinkedIn] Suchbegriff '{search_term}' nicht im Profil gefunden.\n")

def facebook_search_script():
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time
    import os
    from dotenv import load_dotenv
    import concurrent.futures
    import re
    import sys

    # Lade Umgebungsvariablen
    load_dotenv()

    # Facebook Login-Daten aus Umgebungsvariablen
    email = ''
    password = ''

    # Überprüfe, ob die Zugangsdaten gesetzt sind
    if not email or not password:
        print("Fehler: Facebook-Zugangsdaten sind nicht gesetzt. Bitte überprüfe die Umgebungsvariablen.")
        sys.exit(1)

    # Suchparameter
    name_to_search = name_var
    search_term = srch_var

    # Selenium WebDriver einrichten mit angepassten Optionen
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-webgl')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--headless')  # Headless-Modus aktivieren
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--log-level=3')  # Minimiert die Chrome-Logs
    options.add_argument('--silent')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/112.0.0.0 Safari/537.36')  # Benutzerdefinierter User-Agent

    # Unterdrücke die Standardausgabe von ChromeDriver
    service = Service(ChromeDriverManager().install())
    service.log_file = open(os.devnull, 'w')

    driver = webdriver.Chrome(service=service, options=options)

    def process_profile(profile_url, search_term, found_profiles):
        """Funktion zur Verarbeitung eines einzelnen Profils."""
        try:
            # WebDriver-Optionen für das Profil
            options_profile = Options()
            options_profile.add_argument('--no-sandbox')
            options_profile.add_argument('--disable-dev-shm-usage')
            options_profile.add_argument('--disable-gpu')
            options_profile.add_argument('--disable-webgl')
            options_profile.add_argument('--disable-software-rasterizer')
            options_profile.add_argument('--window-size=1920,1080')
            options_profile.add_argument('--headless')  # Headless-Modus aktivieren
            options_profile.add_argument('--disable-extensions')
            options_profile.add_argument('--disable-infobars')
            options_profile.add_argument('--log-level=3')
            options_profile.add_argument('--silent')
            options_profile.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                                        'Chrome/112.0.0.0 Safari/537.36')  # Benutzerdefinierter User-Agent

            service_profile = Service(ChromeDriverManager().install())
            service_profile.log_file = open(os.devnull, 'w')
            driver_profile = webdriver.Chrome(service=service_profile, options=options_profile)
            driver_profile.get(profile_url)

            # Warte, bis die Seite vollständig geladen ist
            WebDriverWait(driver_profile, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            time.sleep(2)  # Zusätzliche Wartezeit

            # Suche nach dem Suchbegriff im Seitenquelltext
            page_source = driver_profile.page_source.lower()
            if search_term.lower() in page_source:
                found_profiles.append(profile_url)

            # Schließe den WebDriver für dieses Profil
            driver_profile.quit()
        except Exception as e:
            try:
                driver_profile.quit()
            except:
                pass

    try:
        # Öffne Facebook
        driver.get('https://www.facebook.com/')
        time.sleep(3)

        # Logge dich ein
        email_field = driver.find_element(By.ID, 'email')
        password_field = driver.find_element(By.ID, 'pass')
        email_field.send_keys(email)
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)

        # Überprüfe, ob das Login erfolgreich war
        if "login" in driver.current_url.lower():
            print("Fehler: Login fehlgeschlagen. Bitte überprüfe deine Zugangsdaten.")
            sys.exit(1)

        # Führe die Suche durch
        search_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='search']"))
        )
        search_box.send_keys(name_to_search)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)

        # Überprüfe, ob der Personen-Filter vorhanden ist
        people_filter = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Personen']"))
        )

        # Klicke auf "Alle ansehen" innerhalb der "Personen" Sektion
        alle_ansehen_button_xpath = "//div[contains(., 'Personen')]/following-sibling::div//a[@aria-label='Alle ansehen']"
        alle_ansehen_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, alle_ansehen_button_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", alle_ansehen_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", alle_ansehen_button)
        time.sleep(5)

        # Funktion zum dynamischen Scrollen mit Pausen (max 3 Scrolls)
        def scroll_to_load_profiles(driver, pause_time=2, max_scrolls=3):
            last_height = driver.execute_script("return document.body.scrollHeight")
            scrolls = 0
            while scrolls < max_scrolls:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(pause_time)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scrolls += 1

        # Scrolle, um mehr Profile zu laden
        scroll_to_load_profiles(driver)

        # Sammle alle einzigartigen Profil-URLs
        profiles = driver.find_elements(By.XPATH, "//a[contains(@href, '/profile.php?id=')]")
        profile_urls = set()
        for profile in profiles:
            profile_url = profile.get_attribute('href')
            if profile_url and re.match(r'https?://www\.facebook\.com/profile\.php\?id=\d+', profile_url):
                profile_urls.add(profile_url)

        print(f"Anzahl eindeutiger Profile zur Verarbeitung: {len(profile_urls)}")

        if profile_urls:
            print("\nStarte die Verarbeitung der gefundenen Profile...")
            found_profiles = []
            max_threads = 5
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = {executor.submit(process_profile, url, search_term, found_profiles): url for url in profile_urls}
                for idx, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                    try:
                        future.result()
                        print(f"Verarbeite Profil {idx}/{len(profile_urls)}")
                    except:
                        pass

            # Ausgabe der gefundenen Treffer
            if found_profiles:
                print("\nGefundene Treffer:")
                for url in found_profiles:
                    print(f"{url}")
            else:
                print("\nKeine Treffer gefunden.")

        else:
            print(f"\nKeine Profile mit dem Suchbegriff '{search_term}' gefunden.")

    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    finally:
        driver.quit()
    try:
        print(alpha)
    except NameError:
        print("Variable 'alpha' is not defined.")
    try:
        print(beta)
    except NameError:
        print("Variable 'beta' is not defined.")
    
def main():
    print("Starte die Google-Suche...")
    google_search_script()
    
    print("\nStarte die LinkedIn-Suche...")
    linkedin_search_script()
    
    print("\nStarte die Facebook-Suche...")
    facebook_search_script()

if __name__ == "__main__":
    main()
