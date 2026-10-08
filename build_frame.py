"""Build the sampling frame (department x eligible-faculty roster) from the official
Scholars@Duke widgets API (organizations/people for the Trinity College org).

One API call. Only frame fields are kept (name, title, dept, profile URL); bios,
images, and other profile content are discarded before anything is written.

Outputs:
  roster_all.csv  dept, division, name, rank, title, profile_url   (eligible only)
  frame.csv       dept, division, M_i, flag, roster_source_url
"""
import csv
import json
import re
import urllib.request
from collections import Counter

API = "https://scholars.duke.edu/widgets/api/v0.9/organizations/people/all.json?uri="
TRINITY = "https://scholars.duke.edu/individual/org50000491"

# Trinity departments -> division. None = not a department (program/center/etc.), excluded.
# flag = classification worth a human check.
DEPTS = {
    # Humanities
    "Art, Art History & Visual Studies": ("Humanities", ""),
    "Asian & Middle Eastern Studies": ("Humanities", ""),
    "Classical Studies": ("Humanities", ""),
    "English": ("Humanities", ""),
    "German Studies": ("Humanities", ""),
    "Literature": ("Humanities", ""),
    "Music": ("Humanities", ""),
    "Philosophy": ("Humanities", ""),
    "Religious Studies": ("Humanities", ""),
    "Romance Studies": ("Humanities", ""),
    "Slavic & Eurasian Studies": ("Humanities", ""),
    "Theater Studies": ("Humanities", ""),
    # Social Sciences
    "African & African American Studies": ("Social Sciences", ""),
    "Cultural Anthropology": ("Social Sciences", ""),
    "Economics": ("Social Sciences", ""),
    "Gender, Sexuality & Feminist Studies": ("Social Sciences", ""),
    "History": ("Social Sciences", ""),
    "Political Science": ("Social Sciences", ""),
    "Sociology": ("Social Sciences", ""),
    # Natural Sciences
    "Biology": ("Natural Sciences", ""),
    "Chemistry": ("Natural Sciences", ""),
    "Computer Science": ("Natural Sciences", ""),
    "Evolutionary Anthropology": ("Natural Sciences", ""),
    "Mathematics": ("Natural Sciences", ""),
    "Physics": ("Natural Sciences", ""),
    "Psychology & Neuroscience": ("Natural Sciences", "cross-listed by Trinity in Natural AND Social Sciences"),
    "Statistical Science": ("Natural Sciences", ""),
}
# Units seen in the Trinity feed that we treat as non-departments (excluded). Listed so
# any unit not in either dict gets reported instead of silently dropped.
NON_DEPTS = {
    "Dance Program", "Writing and Rhetoric Program", "Linguistics", "Cinematic Arts",
    "Computational Media, Arts & Cultures", "Education", "Education Program",
    "Masters of Fine Arts in Experimental and Documentary Arts",
    "Trinity College of Arts & Sciences", "Sperling Center for Jewish Studies",
    "International Comparative Studies", "Markets & Management Studies",
    "Army Reserve Officer Training Corps (ROTC)",
    "Air Force Reserve Officer Training Corps (ROTC)", "Information Science + Studies",
    "Asian Pacific Studies Institute", "FOCUS Program",
}

RANK_RE = re.compile(r"^(Assistant |Associate )?Professor\b")
EXCLUDE_RE = re.compile(r"Emerit|Practice|Research|Adjunct|Visiting|Clinical|Lectur|Instructor",
                        re.I)


def rank_of(title):
    if not title or EXCLUDE_RE.search(title):
        return None
    m = RANK_RE.match(title)
    if not m:
        return None
    return {"Assistant ": "Assistant", "Associate ": "Associate", None: "Full"}[m.group(1)]


def main():
    req = urllib.request.Request(API + TRINITY,
                                 headers={"User-Agent": "STA322 class project (frame build)"})
    rows = json.load(urllib.request.urlopen(req, timeout=60))

    roster, unknown_units = [], Counter()
    for r in rows:
        a = r["attributes"]
        if not a.get("positionType", "").endswith("#PrimaryPosition"):
            continue
        org = a.get("organizationName")
        if org not in DEPTS:
            if org not in NON_DEPTS:
                unknown_units[org] += 1
            continue
        rank = rank_of(r.get("title"))
        if rank is None:
            continue
        roster.append({"dept": org, "division": DEPTS[org][0], "name": r["label"],
                       "rank": rank, "title": r["title"], "profile_url": a["profileURL"]})

    # one primary position per person, but guard anyway
    seen, dedup = set(), []
    for p in sorted(roster, key=lambda p: (p["division"], p["dept"], p["name"])):
        if p["profile_url"] not in seen:
            seen.add(p["profile_url"])
            dedup.append(p)

    with open("roster_all.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dept", "division", "name", "rank", "title",
                                          "profile_url"])
        w.writeheader()
        w.writerows(dedup)

    counts = Counter(p["dept"] for p in dedup)
    with open("frame.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dept", "division", "M_i", "flag", "roster_source_url"])
        for dept, (div, flag) in sorted(DEPTS.items(), key=lambda kv: (kv[1][0], kv[0])):
            w.writerow([dept, div, counts[dept], flag, API + TRINITY])

    print(f"{len(dedup)} eligible faculty in {len(counts)} departments")
    if unknown_units:
        print("UNCLASSIFIED units (excluded, please review):", dict(unknown_units))


if __name__ == "__main__":
    main()
