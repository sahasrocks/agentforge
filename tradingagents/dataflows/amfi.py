import requests

_AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"
_TIMEOUT = 20


def get_all_funds() -> dict[str, dict]:
    """Fetch and parse the full AMFI NAV file.

    Returns a dict of scheme_code (str) → {name, nav, date, category, amc}.

    AMFI file format (semicolon-separated):
    Scheme Code;ISIN Div Payout / ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date
    Category / AMC lines begin without a digit.
    """
    try:
        resp = requests.get(_AMFI_NAV_URL, timeout=_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        return {"error": str(e)}

    funds: dict[str, dict] = {}
    current_category = ""
    current_amc      = ""

    for raw_line in resp.text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Category / AMC header lines don't start with a digit
        if not line[0].isdigit():
            # AMC name lines contain "Mutual Fund" or "Asset Management"
            if "Mutual Fund" in line or "Asset Management" in line or "AMC" in line:
                current_amc = line
            else:
                current_category = line
            continue

        parts = line.split(";")
        if len(parts) < 6:
            continue

        scheme_code = parts[0].strip()
        scheme_name = parts[3].strip()
        nav         = parts[4].strip()
        date        = parts[5].strip()

        funds[scheme_code] = {
            "name":     scheme_name,
            "nav":      nav,
            "date":     date,
            "category": current_category,
            "amc":      current_amc,
        }

    return funds


def get_fund_by_name(name_query: str) -> str:
    """Search AMFI fund list by partial name match."""
    funds = get_all_funds()
    if "error" in funds:
        return f"<AMFI data unavailable: {funds['error']}>"

    query   = name_query.lower()
    matches = [
        (code, info)
        for code, info in funds.items()
        if query in info["name"].lower()
    ]

    if not matches:
        return f"No AMFI funds found matching '{name_query}'."

    lines = [f"AMFI funds matching '{name_query}':"]
    for i, (code, info) in enumerate(matches[:20], 1):
        lines.append(f"  {i:2d}. [{code}] {info['name']}  NAV: {info['nav']} ({info['date']})")

    return "\n".join(lines)


def get_category_funds(category: str) -> str:
    """List all funds in a given SEBI category."""
    funds = get_all_funds()
    if "error" in funds:
        return f"<AMFI data unavailable: {funds['error']}>"

    query   = category.lower()
    matches = [
        (code, info)
        for code, info in funds.items()
        if query in info.get("category", "").lower()
    ]

    if not matches:
        return f"No funds found in category '{category}'."

    lines = [f"Funds in category '{category}' ({len(matches)} total):"]
    for i, (code, info) in enumerate(matches[:30], 1):
        lines.append(f"  {i:2d}. [{code}] {info['name']}")

    return "\n".join(lines)
