"""Annotate the 1,440-person Scholars search list (Trinity + Faculty filter) with
eligibility for the target population.

Inputs:
  scholars_trinity_faculty.tsv  slug, name, title   (from the scholars.duke.edu search page)
  roster_all.csv                eligible tenure-track faculty with a Trinity primary
                                appointment (from build_frame.py)
Output:
  frame_1440.csv  slug, profile_url, name, title, eligible, dept, division, rank, exclusion_reason
"""
import csv
import re

search = list(csv.DictReader(open("scholars_trinity_faculty.tsv"), delimiter="\t"))
elig = {r["profile_url"].rsplit("/", 1)[1]: r for r in csv.DictReader(open("roster_all.csv"))}


def reason(title):
    if not title:
        return "not tenure-track, or primary appointment outside Trinity departments (title not shown)"
    for pat, why in [("Emerit", "emeritus"), ("Practice", "professor of the practice"),
                     ("Lectur|Instruct|Staff", "lecturer/instructor"),
                     ("Research", "research faculty"), ("Adjunct", "adjunct"),
                     ("Visiting", "visiting")]:
        if re.search(pat, title):
            return why
    return "primary appointment outside Trinity departments, or non-faculty title"


with open("frame_1440.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["slug", "profile_url", "name", "title", "eligible", "dept", "division", "rank",
                "exclusion_reason"])
    for p in search:
        e = elig.get(p["slug"])
        w.writerow([p["slug"], "https://scholars.duke.edu/person/" + p["slug"], p["name"],
                    p["title"], int(e is not None), e["dept"] if e else "",
                    e["division"] if e else "", e["rank"] if e else "",
                    "" if e else reason(p["title"])])

print(f"{len(search)} people, {len(elig)} eligible")
