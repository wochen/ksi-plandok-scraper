# Dockerfile - UŻYWA OFICJALNEGO SELENIUM
FROM selenium/standalone-chrome:latest

# Instaluj Python i dependencies
USER root
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install selenium python-dotenv

# Kopiuj pliki
COPY scraper.py /app/scraper.py
COPY .env /app/.env
WORKDIR /app

CMD ["python3", "/app/scraper.py"]
