import re

_PHONE_RE = re.compile(
    r'(\+?1[\s.-]?)?'          # optional country code
    r'(\(?\d{3}\)?[\s.-]?)'    # area code
    r'(\d{3}[\s.-]?)'          # exchange
    r'(\d{4})'                 # number
)


def redact_reports(reports: list[dict]) -> list[dict]:
    """Full redaction: alias replaced in field and rawText, contact removed."""
    redacted = []
    for report in reports:
        r = report.copy()
        raw = r.get("rawText", "") or ""
        alias = r.get("heroAlias")
        if alias:
            raw = re.sub(re.escape(alias), "[REDACTED]", raw, flags=re.IGNORECASE)
        raw = _PHONE_RE.sub("[REDACTED]", raw)
        r["rawText"] = raw
        r["heroAlias"] = "[REDACTED]"
        r.pop("heroContact", None)
        redacted.append(r)
    return redacted


def redact_contact(reports: list[dict]) -> list[dict]:
    """Light redaction: keeps hero alias visible, removes contact info and phone numbers from rawText."""
    redacted = []
    for report in reports:
        r = report.copy()
        raw = r.get("rawText", "") or ""
        raw = _PHONE_RE.sub("[REDACTED]", raw)
        r["rawText"] = raw
        r.pop("heroContact", None)
        redacted.append(r)
    return redacted
