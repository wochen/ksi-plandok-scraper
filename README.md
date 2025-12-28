# KSI Booking Scraper 🎯

Prosty bot napisany w Pythonie (Selenium), który sprawdza dostępność terminów na strzelnicy **KSI (Klub Strzelających Inaczej)** w systemie Plandok i wysyła raport e-mailem.

Projekt jest udostępniony jako Open Source – każdy może z niego korzystać, dostosować go do swoich potrzeb lub uruchomić na własnym serwerze/komputerze.

## 🚀 Możliwości
- Automatyczne wchodzenie na stronę rezerwacji.
- Wybór usługi (domyślnie 30 min, konfigurowalne).
- Przechodzenie przez kalendarz na 7 dni w przód.
- Pobieranie wolnych godzin.
- Wysyłanie raportu na e-mail (Gmail).

## 🛠️ Wymagania
- Docker (zalecane) LUB Python 3.9+ z zainstalowanym Chrome i ChromeDriver.

## ⚙️ Konfiguracja
W pliku `scraper.py` znajdź sekcję **KONFIGURACJA** i uzupełnij:

```python
FROM_EMAIL = "twoj_adres@gmail.com"
TO_EMAIL = "gdzie_wyslac_raport@gmail.com"
EMAIL_PASSWORD = "twoje_haslo_aplikacji"  # Wygeneruj w Google: Security > App Passwords
