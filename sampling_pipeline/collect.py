"""Step 6: collect the survey variables for the 124 sampled faculty only.

For each person in sample.csv we make two throttled requests: their public profile page
(to find their internal Scholars ID) and their record in the Scholars@Duke data feed.
Only the variables needed for the four research questions are kept.

Coding rules
  sex             left blank; coded by hand from each profile (1 = female, 0 = male)
  grant_2026      1 if any grant, fellowship or gift runs at some point in 2026, else 0
                  (also 0 when none are listed); an award with no end date counts as
                  lasting only its start year
  has_phd         1 if a Ph.D. or D.Phil. is listed, 0 if education is listed without one,
                  blank if no education is listed
  years_since_phd 2026 minus the year of the earliest PhD
  phd_duke        1 if that PhD is from Duke University (blank unless has_phd = 1)

Writes data.csv.
"""
import csv
import json
import re
import time
import urllib.request

FEED = "https://scholars.duke.edu/widgets/api/v0.9/people/complete/all.json?uri="
HEADERS = {"User-Agent": "STA322 class project (sampled profiles only)"}
PAUSE = 1.5      # seconds between requests
YEAR = 2026
PHD = re.compile(r"^(Ph\.?\s?D\.?|D\.?\s?Phil\.?|Doctor of Philosophy)$", re.I)
DESIGN = ["name", "dept", "M_h", "n_h", "pi", "w"]


def fetch(url):
    """GET a URL as text, retrying twice after a short wait."""
    request = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            return urllib.request.urlopen(request, timeout=60).read().decode("utf-8")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5)


def year(date):
    return int(date[:4]) if date else None


def earliest_phd(educations):
    """(has_phd, year, institution) for a person's earliest PhD."""
    if not educations:
        return None, None, ""
    phds = []
    for edu in educations:
        info = edu.get("attributes", {})
        if PHD.match((info.get("degree") or "").strip()):
            phds.append((year(info.get("endDate")), info.get("institution") or ""))
    if not phds:
        return 0, None, ""
    phd_year, institution = min(phds, key=lambda p: (p[0] is None, p[0]))  # missing years last
    return 1, phd_year, institution


def has_grant_in(year_wanted, awards):
    """True if any award's start-end period includes the given year."""
    for award in awards:
        info = award.get("attributes", {})
        start = info.get("startDate") or info.get("dateTimeStart")   # gifts use dateTime*
        end = info.get("endDate") or info.get("dateTimeEnd") or start
        if (year(start) or 0) <= year_wanted <= (year(end) or 0):
            return True
    return False


def code_person(record):
    has_phd, phd_year, institution = earliest_phd(record.get("educations") or [])
    awards = (record.get("grants") or []) + (record.get("gifts") or [])
    return {
        "sex": "",
        "grant_2026": int(has_grant_in(YEAR, awards)),
        "has_phd": "" if has_phd is None else has_phd,
        "years_since_phd": YEAR - phd_year if phd_year else "",
        "phd_duke": int("Duke University" in institution) if has_phd == 1 else "",
    }


def main():
    sample = list(csv.DictReader(open("sample.csv")))
    rows = []
    for i, person in enumerate(sample, 1):
        page = fetch(person["profile_url"])
        time.sleep(PAUSE)
        scholars_id = re.search(r"https://scholars\.duke\.edu/individual/per\d+", page)
        if not scholars_id:
            raise SystemExit(f"could not resolve person URI for {person['profile_url']}")
        record = json.loads(fetch(FEED + scholars_id.group(0)))
        time.sleep(PAUSE)

        rows.append({**{k: person[k] for k in DESIGN}, **code_person(record)})
        print(f"[{i}/{len(sample)}] {person['name']}", flush=True)

    with open("data.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote data.csv ({len(rows)} rows)")


if __name__ == "__main__":
    main()
