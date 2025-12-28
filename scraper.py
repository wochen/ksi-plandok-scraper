# scraper.py - WERSJA MULTI-BCC
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, timedelta
import time
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Jeśli nie ma dotenv, zmienne muszą być ustawione ręcznie

DEBUG = False

# ================== KONFIGURACJA ==================
PUBLIC_URL = "https://book.plandok.com/stowarzyszenie-ksi"
LINK_DLA_UZYTKOWNIKA = "https://book.plandok.com/pl/stowarzyszenie-ksi"

# --- POBIERANIE DANYCH Z ZMIENNYCH ŚRODOWISKOWYCH ---
FROM_EMAIL = os.environ.get("FROM_EMAIL")
TO_EMAIL = os.environ.get("TO_EMAIL")

# Jeśli nie podano BCC, zostawiamy pustą listę
bcc_str = os.environ.get("BCC_EMAILS", "")
BCC_EMAILS = [email.strip() for email in bcc_str.split(",")] if bcc_str else []

EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

USLUGA_CZAS = os.environ.get("USLUGA_CZAS", "30")  # Domyślnie 30

GODZINY_OTWARCIA = {
    0: (16, 22), 1: (16, 22), 2: (16, 22), 3: (16, 22),
    4: (10, 22), 5: (10, 22), 6: (10, 22)
}
SLOT_KROK = 30

DNI_TYGODNIA = {
    0: "Poniedziałek", 1: "Wtorek", 2: "Środa", 3: "Czwartek",
    4: "Piątek", 5: "Sobota", 6: "Niedziela"
}
# ==================================================

def generuj_oczekiwane_sloty(start, end):
    slots = []
    current = start * 60
    koniec = end * 60
    while current < koniec:
        h = current // 60
        m = current % 60
        slots.append(f"{h:02d}:{m:02d}")
        current += SLOT_KROK
    return slots

def wyslij_mail(temat, tresc):
    # Stopka z linkiem
    tresc_z_linkiem = f"{tresc}\n\n--\nRezerwacja: {LINK_DLA_UZYTKOWNIKA}"

    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = temat
    msg.attach(MIMEText(tresc_z_linkiem, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(FROM_EMAIL, EMAIL_PASSWORD)

        # --- LOGIKA MULTI-BCC ---
        # Łączymy głównego odbiorcę (jako listę jednoelementową) z listą BCC
        wszyscy_odbiorcy = [TO_EMAIL] + BCC_EMAILS

        server.sendmail(FROM_EMAIL, wszyscy_odbiorcy, msg.as_string())
        server.quit()
        print(f"Mail wysłany do: {TO_EMAIL} oraz ukrytych kopii ({len(BCC_EMAILS)}).")
    except Exception as e:
        print(f"Błąd maila: {e}")

def zrzut_debug(driver, nazwa):
    try:
        timestamp = datetime.now().strftime("%H%M%S")
        base_path = f"/app/debug_{timestamp}_{nazwa}"
        driver.save_screenshot(f"{base_path}.png")
        print(f"   [DEBUG] Zrzut: {base_path}.png")
    except Exception as e:
        print(f"   [DEBUG] Błąd zrzutu: {e}")

def scrapuj():
    if DEBUG: print("Debug: Rozpoczynam funkcję scrapuj()")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    if DEBUG: print("Debug: Tworzę instancję WebDriver")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    if DEBUG: print("Debug: WebDriver utworzony")

    try:
        print("1. Ładuję stronę główną...")
        driver.get(PUBLIC_URL)
        if DEBUG: print(f"Debug: URL załadowany: {PUBLIC_URL}")
        time.sleep(5)
        if DEBUG: print("Debug: Czekanie 5 sekund zakończone")

        # --- KROK 0: KLIKNIĘCIE "BOOK NOW" ---
        print("   Szukam przycisku 'Book now'...")
        try:
            book_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Book now')]")))
            if DEBUG: print("Debug: Znaleziono przycisk Book now")
            driver.execute_script("arguments[0].click();", book_btn)
            print("   -> Kliknięto 'Book now'!")
            time.sleep(3)
            if DEBUG: print("Debug: Czekanie po kliknięciu Book now zakończone")
        except Exception as e:
            print(f"   -> Nie znaleziono 'Book now' (może jesteśmy niżej?): {e}")
            if DEBUG: print("Debug: Błąd podczas szukania Book now")

        # 1a. ZAMYKANIE COOKIES
        try:
            cookies = driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow') or contains(text(), 'Zgadzam')]")
            if cookies:
                driver.execute_script("arguments[0].click();", cookies[0])
                time.sleep(1)
        except: pass

        # === KROK 2: WYBÓR USŁUGI (ActionChains) ===
        print(f"2. Wybieram usługę {USLUGA_CZAS} min...")
        target_time = USLUGA_CZAS
        xpath_label = f"//div[contains(@id, 'service_')][.//div[text()='{target_time}']][.//div[text()='min']]//label"
        if DEBUG: print(f"Debug: XPath dla usługi: {xpath_label}")

        try:
            label_elem = wait.until(EC.visibility_of_element_located((By.XPATH, xpath_label)))
            if DEBUG: print("Debug: Znaleziono element label dla usługi")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label_elem)
            time.sleep(1)

            actions = ActionChains(driver)
            actions.move_to_element(label_elem).click().perform()
            print("   -> Kliknięto label (ActionChains)!")
            time.sleep(2)
            if DEBUG: print("Debug: Czekanie po wyborze usługi zakończone")

        except Exception as e:
            print(f"   !!! Błąd wyboru usługi: {e}")
            if DEBUG: print("Debug: Błąd podczas wyboru usługi")
            zrzut_debug(driver, "error_wybor_uslugi")

        # === KLIKNIĘCIE NEXT ===
        try:
            next_btn = driver.find_element(By.XPATH, "//button[contains(., 'Next')]")
            if DEBUG: print("Debug: Znaleziono przycisk Next")
            driver.execute_script("arguments[0].click();", next_btn)
            print("   -> Kliknięto NEXT")
        except Exception as e:
            print(f"   Błąd klikania Next: {e}")
            if DEBUG: print("Debug: Błąd podczas klikania Next")

        time.sleep(3)
        if DEBUG: print("Debug: Czekanie 3 sekund po Next zakończone")

        if len(driver.find_elements(By.XPATH, "//button[contains(., 'Next')]")) > 0:
             if DEBUG: print("Debug: Nadal widoczny przycisk Next - błąd przejścia")
             zrzut_debug(driver, "02_fail_still_on_service")
             raise Exception("Nadal jesteśmy na stronie wyboru usługi.")

        print("3. Jesteśmy w kalendarzu. Rozpoczynam analizę...")
        podsumowanie = f"Dostępność KSI Zawodników Gdańsk z Plandok ({USLUGA_CZAS} min) – kolejne 7 dni\n\n"
        today = datetime.now().date()
        if DEBUG: print(f"Debug: Dzisiejsza data: {today}")

        for i in range(7):
            day = today + timedelta(days=i)
            day_num = str(day.day)
            nazwa_dnia = DNI_TYGODNIA.get(day.weekday(), "Nieznany")
            day_str = f"{day.strftime('%d.%m.%Y')} ({nazwa_dnia})"
            if DEBUG: print(f"Debug: Analizuję dzień {i+1}: {day_str}")

            godziny = GODZINY_OTWARCIA.get(day.weekday())
            if DEBUG: print(f"Debug: Godziny otwarcia dla dnia {day.weekday()}: {godziny}")

            if not godziny:
                podsumowanie += f"{day_str}: Zamknięte\n\n"
                if DEBUG: print("Debug: Dzień zamknięty, pomijam")
                continue

            print(f"   Analizuję {day_str}...")

            found_day = False
            slider_attempts = 0
            no_slots = False  # Inicjalizuj tutaj

            while not found_day and slider_attempts < 4:
                try:
                    xpath_candidates = f"//span[normalize-space(text()) = '{day_num}']"
                    candidates = driver.find_elements(By.XPATH, xpath_candidates)

                    for cand in candidates:
                        if cand.is_displayed():
                            parent = cand.find_element(By.XPATH, "./..")
                            if parent.get_attribute("disabled") is not None:
                                if DEBUG: print(f"Debug: Dzień {day_str} jest disabled - brak slotów")
                                no_slots = True
                                found_day = True
                            else:
                                driver.execute_script("arguments[0].click();", parent)
                                time.sleep(1.5)
                                found_day = True
                            break
                    if found_day: break
                except: pass

                if not found_day:
                    try:
                        arrows = driver.find_elements(By.XPATH, "//*[name()='svg' and @viewBox='0 0 18 15']")
                        if len(arrows) > 0:
                            right_arrow = arrows[-1]
                            driver.execute_script("arguments[0].click();", right_arrow.find_element(By.XPATH, "./.."))
                            time.sleep(1.5)
                            slider_attempts += 1
                        else: break
                    except: break

            if not found_day:
                podsumowanie += f"{day_str}: Nie znaleziono w kalendarzu\n\n"
                continue

            # === POBIERANIE SLOTÓW ===
            oczekiwane = generuj_oczekiwane_sloty(godziny[0], godziny[1])
            if DEBUG: print(f"Debug: Oczekiwane sloty: {oczekiwane}")
            wolne = set()
            if DEBUG: print("Debug: Inicjalizacja zbioru wolne zakończona")

            if no_slots:
                if DEBUG: print("Debug: Dzień disabled lub brak slotów, pomijam zbieranie")
            else:
                if "don't have any available times" in driver.page_source:
                    no_slots = True
                    if DEBUG: print("Debug: Znaleziono komunikat 'don't have any available times'")

                if not no_slots:
                    try:
                        xpath_slots = "//*[contains(text(), ':')]"
                        elements = driver.find_elements(By.XPATH, xpath_slots)
                        if DEBUG: print(f"Debug: Znaleziono {len(elements)} elementów zawierających ':'")
                        for el in elements:
                            if not el.is_displayed(): continue
                            txt = el.text.strip()
                            if 4 <= len(txt) <= 5 and txt[0].isdigit() and ":" in txt:
                                 wolne.add(txt)
                        if DEBUG: print(f"Debug: Zebrane wolne sloty: {wolne}")
                    except: pass
                else:
                    if DEBUG: print("Debug: Brak slotów, pomijam zbieranie")

            count_free = 0
            podsumowanie += f"{day_str}:\n"
            for slot in oczekiwane:
                if slot in wolne:
                    podsumowanie += f"  {slot} – Wolny\n"
                    count_free += 1

            if count_free == 0:
                podsumowanie += "  Brak wolnych terminów\n"
            podsumowanie += "\n"

        return podsumowanie
        if DEBUG: print("Debug: Funkcja scrapuj() zakończona sukcesem")

    except Exception as e:
        print("!!! WYSTĄPIŁ BŁĄD KRYTYCZNY !!!")
        print(traceback.format_exc())
        if DEBUG: print(f"Debug: Szczegóły błędu: {e}")
        zrzut_debug(driver, "99_CRITICAL_ERROR")
        return f"Błąd krytyczny: {str(e)}"
    finally:
        if DEBUG: print("Debug: Zamykam WebDriver")
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '-v':
        DEBUG = True
        print("Debugowanie włączone")
    raport = scrapuj()
    temat = f"Raport KSI Zawodników z Plandok ({USLUGA_CZAS} min) – {datetime.now().strftime('%d.%m.%Y')}"
    print("================ RAPORT KOŃCOWY ================")
    print(raport)
    if "Błąd krytyczny" not in raport:
        wyslij_mail(temat, raport)
