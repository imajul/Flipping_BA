import asyncio
import random
import re
import statistics
from typing import List, Optional, Tuple
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

BARRIO_SLUG_ZP = {
    "Belgrano": "belgrano",
    "Palermo": "palermo",
    "Recoleta": "recoleta",
    "Caballito": "caballito",
    "Núñez": "nunez",
    "Villa Crespo": "villa-crespo",
    "Almagro": "almagro",
    "San Telmo": "san-telmo",
    "Barracas": "barracas",
    "Devoto": "devoto",
}

BARRIO_SLUG_ML = {
    "Belgrano": "belgrano",
    "Palermo": "palermo",
    "Recoleta": "recoleta",
    "Caballito": "caballito",
    "Núñez": "nunez",
    "Villa Crespo": "villa-crespo",
    "Almagro": "almagro",
    "San Telmo": "san-telmo",
    "Barracas": "barracas",
    "Devoto": "villa-devoto",
}

TIPO_PREFIX_ZP = {
    "Departamento 2 amb": "departamentos-2-ambientes",
    "Departamento 3 amb": "departamentos-3-ambientes",
    "PH": "ph",
}

TIPO_PATH_ML = {
    "Departamento 2 amb": "departamentos/2-ambientes",
    "Departamento 3 amb": "departamentos/3-ambientes",
    "PH": "ph",
}

EXCLUDES_ZP = ["a estrenar", "en pozo", "en construcción", "construccion", "pozo"]


def _rand_delay():
    return random.uniform(2.0, 5.0)


def _parse_usd(text: str) -> Optional[float]:
    if not text:
        return None
    text = text.upper()
    if "USD" not in text and "U$S" not in text and "US$" not in text and "$" not in text:
        return None
    nums = re.findall(r"[\d.,]+", text)
    for n in nums:
        n = n.replace(".", "").replace(",", "")
        try:
            val = float(n)
            if val > 5000:
                return val
        except ValueError:
            continue
    return None


def _parse_m2(text: str) -> Optional[float]:
    if not text:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", text, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(",", "."))
    return None


def _parse_int(text: str) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None


async def _new_page(browser, barrio_slug: str):
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        locale="es-AR",
        extra_http_headers={
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    page = await context.new_page()
    return page


# ── ZonaProp ───────────────────────────────────────────────────────────────────

async def scrape_zonaprop(
    barrio: str,
    tipo_propiedad: str,
    presupuesto_max: float,
    max_results: int = 20,
) -> Tuple[List[dict], Optional[float]]:
    slug = BARRIO_SLUG_ZP.get(barrio, barrio.lower().replace(" ", "-"))
    tipo_prefix = TIPO_PREFIX_ZP.get(tipo_propiedad, "departamentos")
    url = f"https://www.zonaprop.com.ar/{tipo_prefix}-venta-{slug}.html"

    properties = []
    precio_ref_m2 = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await _new_page(browser, slug)
        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(_rand_delay())

            # Try to get posting cards — ZonaProp uses data-qa attributes
            cards = await page.query_selector_all('[data-qa="posting RESULTS_LIST"] [data-qa="posting"]')
            if not cards:
                cards = await page.query_selector_all('[class*="postingCard"]')
            if not cards:
                # Last resort: any article with price
                cards = await page.query_selector_all("article")

            prices_m2_ref = []

            for card in cards[:30]:
                if len(properties) >= max_results:
                    break
                try:
                    prop = await _extract_zonaprop_card(card, barrio, tipo_propiedad)
                    if prop is None:
                        continue

                    # Exclude new construction for reference but include for flipping
                    desc_lower = (prop.get("descripcion") or "").lower()
                    titulo_lower = (prop.get("titulo") or "").lower()
                    is_new = any(ex in desc_lower or ex in titulo_lower for ex in EXCLUDES_ZP)

                    if prop.get("precio_usd") and prop["precio_usd"] <= presupuesto_max:
                        if not is_new:
                            properties.append(prop)
                        # Collect m2 prices for reference (excluding new construction)
                        if prop.get("precio_m2") and not is_new:
                            prices_m2_ref.append(prop["precio_m2"])

                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"ZonaProp card error: {e}")
                    continue

            # If we have few results, also include cheapest properties
            if len(properties) < 5:
                all_cards_data = []
                for card in cards[:30]:
                    try:
                        prop = await _extract_zonaprop_card(card, barrio, tipo_propiedad)
                        if prop and prop.get("precio_usd") and prop["precio_usd"] <= presupuesto_max:
                            all_cards_data.append(prop)
                    except Exception:
                        continue
                all_cards_data.sort(key=lambda x: x.get("precio_usd") or 999999)
                bottom_20pct = all_cards_data[: max(1, len(all_cards_data) // 5)]
                seen_urls = {p["url"] for p in properties}
                for p in bottom_20pct:
                    if p["url"] not in seen_urls:
                        properties.append(p)

            if prices_m2_ref:
                precio_ref_m2 = statistics.median(prices_m2_ref)

        except PlaywrightTimeout:
            print(f"ZonaProp timeout for {url}")
        except Exception as e:
            print(f"ZonaProp error: {e}")
        finally:
            await browser.close()

    return properties, precio_ref_m2


async def _extract_zonaprop_card(card, barrio: str, tipo_propiedad: str) -> Optional[dict]:
    # URL
    link = await card.query_selector("a[href]")
    if not link:
        return None
    href = await link.get_attribute("href")
    if not href:
        return None
    if href.startswith("/"):
        href = "https://www.zonaprop.com.ar" + href
    if "zonaprop.com.ar" not in href:
        return None

    # Title
    titulo_el = await card.query_selector('[data-qa="posting-title"], h2, h3, [class*="title"]')
    titulo = await titulo_el.inner_text() if titulo_el else "Departamento en venta"
    titulo = titulo.strip()[:200]

    # Price
    precio_usd = None
    for sel in ['[data-qa="posting-price"]', '[class*="price"]', '[class*="Price"]']:
        price_el = await card.query_selector(sel)
        if price_el:
            price_text = await price_el.inner_text()
            precio_usd = _parse_usd(price_text)
            if precio_usd:
                break

    if not precio_usd:
        return None

    # Area
    m2 = None
    features_text = ""
    for sel in ['[data-qa="posting-main-features"]', '[class*="features"]', '[class*="Features"]']:
        feat_el = await card.query_selector(sel)
        if feat_el:
            features_text = await feat_el.inner_text()
            m2 = _parse_m2(features_text)
            break

    precio_m2 = round(precio_usd / m2, 0) if m2 and m2 > 0 else None

    # Address
    direccion = None
    for sel in ['[data-qa="posting-location"]', '[class*="address"]', '[class*="location"]']:
        addr_el = await card.query_selector(sel)
        if addr_el:
            direccion = (await addr_el.inner_text()).strip()[:200]
            break

    # Ambientes
    ambientes = None
    m = re.search(r"(\d+)\s*amb", features_text, re.IGNORECASE)
    if m:
        ambientes = int(m.group(1))

    # Baños
    banios = None
    m = re.search(r"(\d+)\s*ba[ñn]", features_text, re.IGNORECASE)
    if m:
        banios = int(m.group(1))

    # Description (from card text)
    desc_el = await card.query_selector('[class*="description"], [class*="Description"], p')
    descripcion = (await desc_el.inner_text()).strip()[:500] if desc_el else features_text[:300]

    return {
        "url": href,
        "titulo": titulo,
        "precio_usd": precio_usd,
        "m2_cubiertos": m2,
        "precio_m2": precio_m2,
        "direccion": direccion,
        "descripcion": descripcion,
        "ambientes": ambientes,
        "banios": banios,
        "tiene_balcon": "balcon" in (descripcion or "").lower() or "balcón" in (descripcion or "").lower(),
        "tiene_cochera": "cochera" in (descripcion or "").lower(),
        "fuente": "zonaprop",
        "barrio": barrio,
        "tipo_propiedad": tipo_propiedad,
    }


# ── MercadoLibre ──────────────────────────────────────────────────────────────

async def scrape_mercadolibre(
    barrio: str,
    tipo_propiedad: str,
    presupuesto_max: float,
    max_results: int = 20,
) -> List[dict]:
    slug = BARRIO_SLUG_ML.get(barrio, barrio.lower().replace(" ", "-"))
    tipo_path = TIPO_PATH_ML.get(tipo_propiedad, "departamentos")
    url = f"https://inmuebles.mercadolibre.com.ar/{tipo_path}/venta/capital-federal/{slug}/"

    properties = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await _new_page(browser, slug)
        try:
            await page.goto(url, timeout=35000, wait_until="networkidle")
            await asyncio.sleep(_rand_delay())

            # MercadoLibre uses Polycard or legacy search-result cards
            cards = await page.query_selector_all("li.ui-search-layout__item")
            if not cards:
                cards = await page.query_selector_all(".andes-card")

            for card in cards[:30]:
                if len(properties) >= max_results:
                    break
                try:
                    prop = await _extract_ml_card(card, barrio, tipo_propiedad)
                    if prop is None:
                        continue
                    if prop.get("precio_usd") and prop["precio_usd"] <= presupuesto_max:
                        properties.append(prop)
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"ML card error: {e}")
                    continue

        except PlaywrightTimeout:
            print(f"MercadoLibre timeout for {url}")
            # Try mobile URL as fallback
            try:
                mobile_url = url.replace(
                    "inmuebles.mercadolibre.com.ar",
                    "inmuebles.mercadolibre.com.ar",
                )
                await page.goto(mobile_url + "?display=list", timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(_rand_delay())
            except Exception:
                pass
        except Exception as e:
            print(f"MercadoLibre error: {e}")
        finally:
            await browser.close()

    return properties


async def _extract_ml_card(card, barrio: str, tipo_propiedad: str) -> Optional[dict]:
    # URL
    link = await card.query_selector("a.poly-component__title, a.ui-search-item__group__element, a[href*='mercadolibre']")
    if not link:
        link = await card.query_selector("a[href]")
    if not link:
        return None
    href = await link.get_attribute("href")
    if not href or "mercadolibre.com.ar" not in href:
        return None
    # Strip tracking params
    href = href.split("?")[0] if "?" in href else href

    # Title
    titulo_el = await card.query_selector(
        ".poly-component__title, .ui-search-item__title, h2, h3"
    )
    titulo = (await titulo_el.inner_text()).strip()[:200] if titulo_el else "Propiedad en venta"

    # Price — MercadoLibre shows USD or ARS
    precio_usd = None
    for sel in [
        ".price-tag-amount",
        ".andes-money-amount__fraction",
        ".price-tag-fraction",
        "[class*='price']",
    ]:
        price_el = await card.query_selector(sel)
        if price_el:
            price_text = await price_el.inner_text()
            # Check currency
            currency_el = await card.query_selector(".price-tag-symbol, .andes-money-amount__currency-symbol")
            currency = (await currency_el.inner_text()).strip() if currency_el else ""
            if "USD" in currency or "US$" in currency or "U$S" in currency:
                nums = re.findall(r"[\d.,]+", price_text)
                for n in nums:
                    n = n.replace(".", "").replace(",", "")
                    try:
                        val = float(n)
                        if val > 5000:
                            precio_usd = val
                            break
                    except ValueError:
                        continue
            if precio_usd:
                break

    if not precio_usd:
        # Try parsing full text
        card_text = await card.inner_text()
        precio_usd = _parse_usd(card_text)

    if not precio_usd:
        return None

    # Features from attribute list
    attrs_text = ""
    attr_els = await card.query_selector_all(".poly-attributes-list__item, .ui-search-item__group__element")
    for el in attr_els:
        t = (await el.inner_text()).strip()
        attrs_text += " " + t

    m2 = _parse_m2(attrs_text)
    precio_m2 = round(precio_usd / m2, 0) if m2 and m2 > 0 else None

    ambientes = None
    m = re.search(r"(\d+)\s*amb", attrs_text, re.IGNORECASE)
    if m:
        ambientes = int(m.group(1))

    banios = None
    m = re.search(r"(\d+)\s*ba[ñn]", attrs_text, re.IGNORECASE)
    if m:
        banios = int(m.group(1))

    # Address
    addr_el = await card.query_selector(".poly-component__location, .ui-search-item__location")
    direccion = (await addr_el.inner_text()).strip()[:200] if addr_el else barrio

    return {
        "url": href,
        "titulo": titulo,
        "precio_usd": precio_usd,
        "m2_cubiertos": m2,
        "precio_m2": precio_m2,
        "direccion": direccion,
        "descripcion": attrs_text.strip()[:400],
        "ambientes": ambientes,
        "banios": banios,
        "tiene_balcon": "balcon" in attrs_text.lower() or "balcón" in attrs_text.lower(),
        "tiene_cochera": "cochera" in attrs_text.lower(),
        "fuente": "mercadolibre",
        "barrio": barrio,
        "tipo_propiedad": tipo_propiedad,
    }


async def get_precio_ref_m2(barrio: str) -> float:
    """Scrape ZonaProp to compute median price/m2 for used properties in the barrio."""
    slug = BARRIO_SLUG_ZP.get(barrio, barrio.lower().replace(" ", "-"))
    url = f"https://www.zonaprop.com.ar/departamentos-venta-{slug}.html"
    prices = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await _new_page(browser, slug)
        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(_rand_delay())

            cards = await page.query_selector_all('[data-qa="posting"] , [class*="postingCard"]')
            for card in cards[:25]:
                try:
                    prop = await _extract_zonaprop_card(card, barrio, "Departamento 2 amb")
                    if not prop:
                        continue
                    desc = (prop.get("descripcion") or "").lower()
                    title = (prop.get("titulo") or "").lower()
                    is_new = any(ex in desc or ex in title for ex in EXCLUDES_ZP)
                    if not is_new and prop.get("precio_m2") and prop["precio_m2"] > 500:
                        prices.append(prop["precio_m2"])
                except Exception:
                    continue
        except Exception as e:
            print(f"Ref price scrape error: {e}")
        finally:
            await browser.close()

    if prices:
        return statistics.median(prices)
    # Fallback reference prices per barrio (USD/m², approximate 2024 market)
    fallback = {
        "Belgrano": 2800,
        "Palermo": 3200,
        "Recoleta": 3500,
        "Caballito": 2200,
        "Núñez": 2600,
        "Villa Crespo": 2400,
        "Almagro": 2000,
        "San Telmo": 2100,
        "Barracas": 1600,
        "Devoto": 1800,
    }
    return fallback.get(barrio, 2200)
