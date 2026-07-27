"""
Read sop-library/*.md, produce sops.json.

The markdown files are the source of truth. Everything downstream — the portal
library, acknowledgments, the derived job duties — is generated from them, so a
document and its record can't drift apart.
"""
import json, os, re, glob

SRC = "sop-library"
BLANK = re.compile(r"_{6,}")


def parse(path):
    raw = open(path, encoding="utf-8").read()
    code = re.search(r"^# (\S+) · (.+)$", raw, re.M)
    doc = {"code": code.group(1), "title": code.group(2).strip()}

    # control table: rows between the header and the first ---
    head = raw.split("\n---\n", 1)[0]
    fields = {}
    for m in re.finditer(r"^\| ([^|]+?) \| (.*?) \|$", head, re.M):
        k, v = m.group(1).strip(), m.group(2).strip()
        if k in ("Field", "---"):
            continue
        fields[k] = v

    def clean(v):
        if v is None:
            return None
        v = re.sub(r"\*\(.*?\)\*", "", v)
        v = v.replace("`", "").replace("**", "").strip()
        return None if (not v or BLANK.search(v)) else v

    doc["version"] = clean(fields.get("Version"))
    status_raw = fields.get("Status", "")
    doc["status"] = "draft" if "draft" in status_raw.lower() else "active"
    doc["pendingApproval"] = "pending approval" in status_raw.lower()

    scope_raw = fields.get("Scope", "")
    # "Not SQF-scoped" must not read as SQF-scoped
    doc["scope"] = ("sqf" if re.search(r"\bSQF\b", scope_raw) and "not sqf" not in scope_raw.lower()
                    else "business")
    doc["docType"] = ("training_program" if doc["code"].startswith("TRN")
                      else "procedure" if doc["scope"] == "sqf" else "role_sop")

    doc["department"] = clean(fields.get("Department"))
    doc["roles"] = [r.strip() for r in (fields.get("Applies to") or "").split("·") if r.strip()]
    doc["owner"] = clean(fields.get("Owner"))
    doc["approver"] = clean(fields.get("Approved by"))
    doc["effectiveDate"] = clean(fields.get("Effective date"))
    doc["reviewCycle"] = clean(fields.get("Review cycle"))
    doc["supersedes"] = clean(fields.get("Supersedes"))
    doc["generatesRecord"] = ("cleaning_log"
                              if "cleaning log" in (fields.get("Records generated") or "").lower()
                              else None)
    doc["criticalControl"] = doc["scope"] == "sqf"
    doc["confidential"] = "Confidential" in scope_raw
    doc["sourceFile"] = os.path.basename(path)
    doc["body"] = raw

    # section headings, for the portal's contents list
    doc["sections"] = re.findall(r"^## (?:\d+\.\s*)?(.+)$", raw, re.M)

    # duties for the careers page: the daily/responsibility bullets, first five
    duties = []
    for block in re.findall(r"^## \d+\. (?:Daily|Responsibilities|Procedure).*?$(.*?)(?=^## |\Z)",
                            raw, re.M | re.S):
        duties += [re.sub(r"[*`]", "", b).strip()
                   for b in re.findall(r"^(?:- |\d+\. )(.+)$", block, re.M)]
    doc["derivedDuties"] = duties[:5]
    return doc


def main():
    docs = [parse(p) for p in sorted(glob.glob(os.path.join(SRC, "*.md")))]

    unresolved = []
    for d in docs:
        gaps = [k for k, v in (("owner", d["owner"]), ("approver", d["approver"]),
                               ("version", d["version"]), ("effective date", d["effectiveDate"]))
                if not v]
        if gaps:
            unresolved.append({"code": d["code"], "missing": gaps})

    out = {
        "_note": ("Generated from sop-library/*.md by tools/sync_sops.py. Do not hand-edit — "
                  "edit the markdown and re-run. Blank control fields are genuinely blank in "
                  "the source and must be filled by the owner before issue."),
        "documents": docs,
        "openItems": {
            "awaitingControlFields": unresolved,
            "awaitingDecision": [
                {"code": "SOP-SLS-001", "item": "New customer target reconciled to 5/week "
                 "(65/quarter) from the previous 30/quarter. Sales Director must confirm."},
                {"code": "SOP-SLS-002", "item": "Five NJ territories have no named owner and no "
                 "defined boundaries. Held in draft."},
            ],
        },
    }
    json.dump(out, open("sops.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"{len(docs)} documents → sops.json")
    for d in docs:
        print(f"  {d['code']:<12} v{str(d['version'] or '—'):<5} {d['scope']:<9} "
              f"{d['status']:<7} roles={len(d['roles'])} duties={len(d['derivedDuties'])}")
    if unresolved:
        print("\n  awaiting control fields:")
        for u in unresolved:
            print(f"    {u['code']}: {', '.join(u['missing'])}")


if __name__ == "__main__":
    main()
