# vco-news — GitHub Action

Scraper automatico delle news di VCO Trasporti, eseguito ogni 3 giorni da GitHub Actions.
Produce `news.json` consumato dall'app iOS VCO Trasporti.

## Struttura
- `.github/workflows/scrape-news.yml` — workflow GitHub Actions
- `scripts/scrape_news.py` — scraper Python (BeautifulSoup + requests)
- `news.json` — output pubblicato (creato dalla prima esecuzione)

## Setup
Vedi `README.md` principale nella cartella padre (sezione 2).

## Formato news.json
```json
[
  {
    "title": "Titolo della news",
    "date": "07/06/2025",
    "description": "Descrizione completa della news...",
    "url": "https://www.vcotrasporti.it/it/news.php"
  }
]
```

## Test locale
```bash
pip install requests beautifulsoup4 lxml
python scripts/scrape_news.py
cat news.json
```

## Modificare la cadenza
In `scrape-news.yml`:
```yaml
schedule:
  - cron: '0 6 */3 * *'   # ogni 3 giorni alle 06:00 UTC
```
Usa https://crontab.guru per testare altre combinazioni.
