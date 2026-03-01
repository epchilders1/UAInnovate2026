import re

def redact_reports(reports: list[dict]) -> list[dict]:
    redacted = []
    for report in reports:
        r = report.copy()
        name_mention_regex = f"{r["heroAlias"]}"
        number_mention_regex = f"{r["heroContact"]}"
        r["heroAlias"] = "[REDACTED]"
        r.pop("heroContact", None)
        redacted.append(r)
    return redacted
