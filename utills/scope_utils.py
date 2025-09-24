import re, json
# --- Robust runner with JSON-salvage + rule-based fallback ---
_COUNTRY_SYNONYMS = {
    "usa": "United States", "us": "United States", "u.s.": "United States",
    "u.s.a": "United States", "uk": "United Kingdom", "u.k.": "United Kingdom"
}
# Small country/region vocab to avoid extra deps (extend if needed)
_COUNTRIES = {
    "united states", "canada", "india", "germany", "france", "united kingdom",
    "china", "japan", "south korea", "australia", "singapore", "thailand",
    "indonesia", "malaysia", "vietnam", "philippines"
}
_REGIONS = {
    "apac": "APAC",
    "emea": "EMEA",
    "eu": "EU",
    "european union": "EU",
    "southeast asia": "Southeast Asia",
    "sea": "Southeast Asia",
    "latin america": "Latin America",
    "middle east": "Middle East"
}
_SECTOR_PHRASES = [
    "ev charging", "electric vehicle charging", "cloud security",
    "fintech payments", "semiconductors", "renewable energy", "saas",
    "ecommerce", "telemedicine", "ai chips", "battery storage"
]

def _cap5(lst):
    return list(dict.fromkeys([x for x in lst if x]))[:5]

def _detect_time_horizon(q):
    ql = q.lower()
    if "last" in ql and ("months" in ql or "years" in ql):
        # extract snippet like "last 12 months"
        m = re.search(r"last\s+\d+\s+(months|month|years|year)", ql)
        detail = m.group(0) if m else "last period"
        return {"type": "past", "detail": detail}
    if re.search(r"\b20\d{2}\b\s*(–|-|to)\s*\b20\d{2}\b", ql):
        return {"type": "past", "detail": re.search(r"\b20\d{2}\b\s*(–|-|to)\s*\b20\d{2}\b", ql).group(0)}
    if re.search(r"\bby\s+20\d{2}\b", ql):
        return {"type": "future", "detail": re.search(r"\bby\s+20\d{2}\b", ql).group(0)}
    return {"type": "unspecified", "detail": ""}

def _fallback_extract(query):
    ql = query.lower()

    # Countries
    countries = set()
    words = re.findall(r"[A-Za-z]+(?:\s+[A-Za-z]+)?", ql)  # crude bigram coverage
    for w in words:
        w_norm = _COUNTRY_SYNONYMS.get(w.strip(), w.strip())
        if w_norm.lower() in _COUNTRIES:
            # capitalize nicely
            countries.add(w_norm.title() if w_norm.lower() not in {"united states", "united kingdom"} else
                          ("United States" if w_norm.lower()=="united states" else "United Kingdom"))

    # Regions
    regions = set()
    for key, norm in _REGIONS.items():
        if re.search(rf"\b{re.escape(key)}\b", ql):
            regions.add(norm)

    # Sectors (phrase match)
    sectors = set()
    for s in _SECTOR_PHRASES:
        if s in ql:
            sectors.add(s.title() if s != "ev charging" else "EV charging")

    # Companies (basic: capitalized tokens that aren’t at sentence start are noisy;
    # for now, rely on explicit names the user writes; empty list if none.)
    companies = []

    # Scale
    scale = "unknown"
    if countries:
        scale = "country"
    elif regions:
        scale = "regional"
    else:
        # if words like "global", "worldwide", "general"
        if re.search(r"\b(global|worldwide|general)\b", ql):
            scale = "global"
        # If query mentions vendors/companies plural but no geo → company-specific? Not necessarily.
        # Leave as global unless specific company names exist.

    return {
        "scale": scale if (countries or regions or re.search(r"\b(global|worldwide|general)\b", ql)) else "global",
        "countries": _cap5(list(countries)),
        "regions": _cap5(list(regions)),
        "sectors": _cap5(list(sectors)),
        "companies": _cap5(companies),
        "time_horizon": _detect_time_horizon(query),
        "confidence": 0.4 if (countries or regions or sectors) else 0.2,
        "notes": "Rule-based fallback",
        "ambiguities": []
    }

def _salvage_json(text: str):
    # Try clean load
    try:
        return json.loads(text)
    except Exception:
        pass
    # Pull first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            return None
    return None