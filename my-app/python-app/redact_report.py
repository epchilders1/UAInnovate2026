def redact_reports(reports: list[dict]) -> list[dict]:
    redacted = []
    for report in reports:
        r = report.copy()
        if "metadata" in r:
            r["metadata"] = r["metadata"].copy()
            r["metadata"]["hero_alias"] = "REDACTED"
            r["metadata"]["secure_contact"] = "REDACTED"
        redacted.append(r)
    return redacted
