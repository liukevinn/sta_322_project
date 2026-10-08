"""Collect survey variables for the SAMPLED faculty only (sample.csv), from the official
Scholars@Duke widgets API (people/complete). Two throttled requests per person: the public
profile page (to resolve the internal person URI) and the API record.

Coding rules
  sex             left blank for manual coding; pronoun_hint counts pronouns in the bio
  grant_2026      1 if any grant/fellowship/gift interval overlaps calendar 2026
                  (start <= 2026-12-31 and end >= 2026-01-01), else 0 (incl. none listed);
                  an award with no end date is treated as lasting only its start year
  has_phd         1 if any Ph.D./D.Phil. listed; 0 if education is listed but no PhD;
                  NA if no education listed
  phd_year        year of the (earliest) PhD; years_since_phd = 2026 - phd_year
  phd_duke        1 if that PhD is from Duke University (NA if has_phd != 1)

Outputs: data.csv, raw_sampled.json (education/grant/gift records + bio, for auditing
         and for manual sex coding)
"""
import csv
import json
import re
import time
import urllib.request

API = "https://scholars.duke.edu/widgets/api/v0.9/people/complete/all.json?uri="
UA = {"User-Agent": "STA322 class project (sampled profiles only)"}
PAUSE = 1.5
YEAR = 2026
PHD_RE = re.compile(r"^(Ph\.?\s?D\.?|D\.?\s?Phil\.?|Doctor of Philosophy)$", re.I)


def get(url):
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            return urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5)


def year(s):
    return int(s[:4]) if s else None


def pronoun_hint(overview):
    text = re.sub(r"<[^>]+>", " ", overview or "").lower()
    she = len(re.findall(r"\b(she|her|hers|herself)\b", text))
    he = len(re.findall(r"\b(he|him|his|himself)\b", text))
    they = len(re.findall(r"\b(they|them|their|theirs|themself|themselves)\b", text))
    return f"she/her:{she} he/him:{he} they/them:{they}"


def code_person(rec):
    notes = []

    # Education
    edus = rec.get("educations") or []
    phds = []
    for e in edus:
        a = e.get("attributes", {})
        if PHD_RE.match((a.get("degree") or "").strip()):
            phds.append((year(a.get("endDate")), a.get("institution") or "", a.get("degree")))
    if not edus:
        has_phd, phd = None, None
        notes.append("no education listed")
    elif phds:
        has_phd = 1
        phds.sort(key=lambda p: (p[0] is None, p[0]))
        phd = phds[0]
        if len(phds) > 1:
            notes.append(f"{len(phds)} PhDs listed; used earliest")
        if phd[0] is None:
            notes.append("PhD year missing")
        if phd[2].lower().startswith("d"):
            notes.append(f"degree '{phd[2]}' coded as PhD")
    else:
        has_phd, phd = 0, None
    degrees_raw = "; ".join(e.get("label", "") for e in edus)

    # Grants (+ gifts/fellowships, which Scholars shows under Sponsored Research)
    awards = [("grant", g) for g in rec.get("grants") or []] + \
             [("gift", g) for g in rec.get("gifts") or []]
    ongoing, dates_raw, no_end = 0, [], 0
    for kind, g in awards:
        a = g.get("attributes", {})
        s = a.get("startDate") or a.get("dateTimeStart")
        e = a.get("endDate") or a.get("dateTimeEnd")
        dates_raw.append(f"{kind}:{(s or '?')[:10]}..{(e or '?')[:10]}")
        if e is None:
            e = s   # no end date: treat as a one-year award in its start year
            no_end += 1
        if (year(s) or 0) <= YEAR and (year(e) or 0) >= YEAR:
            ongoing += 1

    if no_end:
        notes.append(f"{no_end} award(s) with no end date, treated as start year only")
    phd_year = phd[0] if phd else None
    return {
        "sex": "",
        "pronoun_hint": pronoun_hint(rec.get("attributes", {}).get("overview")),
        "grant_2026": 1 if ongoing else 0,
        "n_awards_ongoing_2026": ongoing,
        "n_grants_listed": len(awards),
        "grant_dates_raw": "; ".join(dates_raw),
        "has_phd": "" if has_phd is None else has_phd,
        "phd_year": phd_year or "",
        "years_since_phd": (YEAR - phd_year) if phd_year else "",
        "phd_institution": phd[1] if phd else "",
        "phd_duke": ("" if has_phd != 1 else int(bool(re.search(r"\bDuke University\b", phd[1])))),
        "degrees_raw": degrees_raw,
        "notes": "; ".join(notes),
    }


def main():
    sample = list(csv.DictReader(open("sample.csv")))
    out, raw = [], {}
    for i, p in enumerate(sample, 1):
        page = get(p["profile_url"])
        time.sleep(PAUSE)
        m = re.search(r"https://scholars\.duke\.edu/individual/per\d+", page)
        if not m:
            raise SystemExit(f"could not resolve person URI for {p['profile_url']}")
        rec = json.loads(get(API + m.group(0)))
        time.sleep(PAUSE)

        coded = code_person(rec)
        out.append({"name": p["name"], "profile_url": p["profile_url"],
                    "division": p["division"], "dept": p["dept"], "rank": p["rank"],
                    "title": p["title"], "M_h": p["M_h"], "n_h": p["n_h"], "pi": p["pi"],
                    "w": p["w"], **coded})
        raw[p["profile_url"]] = {k: rec.get(k) for k in ("educations", "grants", "gifts")}
        raw[p["profile_url"]]["overview"] = rec.get("attributes", {}).get("overview")
        print(f"[{i}/{len(sample)}] {p['name']}: phd={coded['has_phd']} "
              f"grant_2026={coded['grant_2026']} {coded['notes']}", flush=True)

    with open("data.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    json.dump(raw, open("raw_sampled.json", "w"), indent=1)
    print(f"wrote data.csv ({len(out)} rows)")


if __name__ == "__main__":
    main()
