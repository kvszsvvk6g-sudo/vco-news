#!/usr/bin/env python3
"""
Scraper delle news di VCO Trasporti.
Estrae titoli, date e descrizioni da https://www.vcotrasporti.it/it/news.php
e produce un file news.json consumato dall'app iOS.
"""
import json
import re
import sys
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

NEWS_URL = "https://www.vcotrasporti.it/it/news.php"
OUT_FILE = "news.json"
USER_AGENT = (
    "Mozilla/5.0 (compatible; VCO-Trasporti-iOS-Bot/1.0; "
    "+https://github.com/BY-DS/vco-news)"
)


def fetch_page(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def parse_news(html: str) -> list[dict]:
    """
    Il sito VCO Trasporti ha una struttura semplice: news dentro div/box con
    un titolo, una data (formato gg/mm/aaaa oppure gg mese aaaa) e una descrizione.
    Questo parser è difensivo: se il markup cambia, cerca pattern noti e scarta
    elementi privi di titolo o testo.
    """
    soup = BeautifulSoup(html, "lxml")
    items = []

    # Strategia 1: cerca article/box con classi note
    candidates = soup.select(
        "article, .news, .news-item, .box-news, .notizia, .card, .post"
    )

    # Strategia 2: fallback a tutte le h2/h3 dentro <main> o dopo "News"
    if not candidates:
        main = soup.select_one("main, #content, #main, body")
        if main:
            candidates = main.find_all(["h2", "h3"])
            # Usa come contenitore il parent della heading
            candidates = [h.parent for h in candidates if h.parent]

    seen_titles = set()

    for elem in candidates:
        title_tag = elem.find(["h1", "h2", "h3", "h4"])
        title = (title_tag.get_text(strip=True) if title_tag else "").strip()

        # Trova data: pattern italiano gg/mm/aaaa o gg-mm-aaaa o testuale
        text = elem.get_text(" ", strip=True)
        date_match = re.search(r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", text)
        date = date_match.group(1) if date_match else ""

        # Descrizione: primo paragrafo o testo dopo il titolo
        desc_tag = elem.find("p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""
        if not description and text:
            # Rimuovi titolo dal testo e tieni prime 300 char
            description = text.replace(title, "").strip()
            description = description[:400].rstrip() + ("…" if len(description) > 400 else "")

        # Link associato
        link_tag = elem.find("a", href=True)
        url = None
        if link_tag and link_tag.get("href"):
            href = link_tag["href"]
            if href.startswith("http"):
                url = href
            elif href.startswith("/"):
                url = "https://www.vcotrasporti.it" + href
            else:
                url = "https://www.vcotrasporti.it/it/" + href.lstrip("./")

        # Filtra elementi non validi
        if not title or len(title) < 4:
            continue
        if title in seen_titles:
            continue
        seen_titles.add(title)

        items.append({
            "title": title,
            "date": date or datetime.now(timezone.utc).strftime("%d/%m/%Y"),
            "description": description or "(Nessuna descrizione disponibile)",
            "url": url or NEWS_URL,
        })

    # Se non abbiamo trovato nulla, almeno una voce placeholder
    if not items:
        items.append({
            "title": "Consulta le news ufficiali VCO Trasporti",
            "date": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
            "description": (
                "Lo scraper non ha trovato aggiornamenti o la pagina news è cambiata. "
                "Vai direttamente al sito per le ultime comunicazioni."
            ),
            "url": NEWS_URL,
        })

    return items


def main():
    try:
        html = fetch_page(NEWS_URL)
    except Exception as e:
        print(f"Errore download {NEWS_URL}: {e}", file=sys.stderr)
        # Non sovrascriviamo il file esistente in caso di errore
        sys.exit(1)

    news = parse_news(html)
    print(f"Trovate {len(news)} news.")

    # Ordina per data (più recenti prima, best-effort)
    def parse_date(d):
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(d, fmt)
            except Exception:
                continue
        return datetime.min

    news.sort(key=lambda x: parse_date(x["date"]), reverse=True)

    # Mantieni solo le prime 30 per pulizia
    news = news[:30]

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    print(f"Scritto {OUT_FILE}")


if __name__ == "__main__":
    main()
