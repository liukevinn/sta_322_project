"""Step 3: cross-check the 1,440-person search list against the eligible frame.

Marks each person from the Scholars search (Trinity + Faculty) as eligible or not, and
gives a reason for each exclusion.

Reads:  scholars_trinity_faculty.tsv, roster_all.csv
Writes: frame_1440.csv
"""
import csv
import re

# Checked in order; the first match is the reason.
EXCLUSION_REASONS = [
    ("Emerit", "emeritus"),
    ("Practice", "professor of the practice"),
    ("Lectur|Instruct|Staff", "lecturer/instructor"),
    ("Research", "research faculty"),
    ("Adjunct", "adjunct"),
    ("Visiting", "visiting"),
]


def exclusion_reason(title):
    if not title:
        return "not tenure-track, or primary appointment outside Trinity departments (title not shown)"
    for pattern, reason in EXCLUSION_REASONS:
        if re.search(pattern, title):
            return reason
    return "primary appointment outside Trinity departments, or non-faculty title"


search_list = list(csv.DictReader(open("scholars_trinity_faculty.tsv"), delimiter="\t"))
eligible = {row["profile_url"].rsplit("/", 1)[1]: row for row in csv.DictReader(open("roster_all.csv"))}

with open("frame_1440.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["slug", "profile_url", "name", "title", "eligible", "dept", "division",
                     "rank", "exclusion_reason"])
    for person in search_list:
        match = eligible.get(person["slug"], {})
        writer.writerow([
            person["slug"], "https://scholars.duke.edu/person/" + person["slug"],
            person["name"], person["title"], int(bool(match)),
            match.get("dept", ""), match.get("division", ""), match.get("rank", ""),
            "" if match else exclusion_reason(person["title"]),
        ])

print(f"{len(search_list)} people, {len(eligible)} eligible")
