"""Step 2: build the sampling frame.

The frame is every tenure-track professor (Assistant, Associate or Full) whose primary
appointment is in one of the 27 Trinity departments. We get every Trinity appointment
from the Scholars@Duke data feed in a single request and keep only the frame fields
(name, title, department, profile link).

Writes roster_all.csv: one row per eligible faculty member.
"""
import csv
import json
import re
import urllib.request
from collections import Counter

SOURCE = ("https://scholars.duke.edu/widgets/api/v0.9/organizations/people/all.json"
          "?uri=https://scholars.duke.edu/individual/org50000491")   # Trinity College

HUM, SOC, NAT = "Humanities", "Social Sciences", "Natural Sciences"

# The 27 Trinity departments and their divisions (from Trinity's division pages).
DIVISION = {
    "Art, Art History & Visual Studies": HUM, "Asian & Middle Eastern Studies": HUM,
    "Classical Studies": HUM, "English": HUM, "German Studies": HUM, "Literature": HUM,
    "Music": HUM, "Philosophy": HUM, "Religious Studies": HUM, "Romance Studies": HUM,
    "Slavic & Eurasian Studies": HUM, "Theater Studies": HUM,

    "African & African American Studies": SOC, "Cultural Anthropology": SOC,
    "Economics": SOC, "Gender, Sexuality & Feminist Studies": SOC, "History": SOC,
    "Political Science": SOC, "Sociology": SOC,

    "Biology": NAT, "Chemistry": NAT, "Computer Science": NAT,
    "Evolutionary Anthropology": NAT, "Mathematics": NAT, "Physics": NAT,
    "Psychology & Neuroscience": NAT, "Statistical Science": NAT,
}

# Trinity units that are programs, centers etc. rather than departments. Anything in the
# feed that is in neither list gets printed so it can't be dropped silently.
NOT_DEPARTMENTS = {
    "Dance Program", "Writing and Rhetoric Program", "Linguistics", "Cinematic Arts",
    "Computational Media, Arts & Cultures", "Education", "Education Program",
    "Masters of Fine Arts in Experimental and Documentary Arts",
    "Trinity College of Arts & Sciences", "Sperling Center for Jewish Studies",
    "International Comparative Studies", "Markets & Management Studies",
    "Army Reserve Officer Training Corps (ROTC)",
    "Air Force Reserve Officer Training Corps (ROTC)", "Information Science + Studies",
    "Asian Pacific Studies Institute", "FOCUS Program",
}

NOT_TENURE_TRACK = re.compile(
    r"Emerit|Practice|Research|Adjunct|Visiting|Clinical|Lectur|Instructor", re.I)
PROFESSOR = re.compile(r"^(Assistant |Associate )?Professor\b")


def rank_of(title):
    """'Assistant', 'Associate' or 'Full' for a tenure-track title, otherwise None."""
    if not title or NOT_TENURE_TRACK.search(title):
        return None
    match = PROFESSOR.match(title)
    return (match.group(1) or "Full").strip() if match else None


def main():
    request = urllib.request.Request(SOURCE, headers={"User-Agent": "STA322 class project (frame build)"})
    appointments = json.load(urllib.request.urlopen(request, timeout=60))

    eligible, unclassified = [], Counter()
    for appt in appointments:
        info = appt["attributes"]
        if not info.get("positionType", "").endswith("#PrimaryPosition"):
            continue
        dept = info.get("organizationName")
        if dept not in DIVISION:
            if dept not in NOT_DEPARTMENTS:
                unclassified[dept] += 1
            continue
        rank = rank_of(appt.get("title"))
        if rank:
            eligible.append({"dept": dept, "division": DIVISION[dept], "name": appt["label"],
                             "rank": rank, "title": appt["title"],
                             "profile_url": info["profileURL"]})

    # Everyone has one primary appointment, but drop duplicate people just in case.
    roster = {}
    for person in sorted(eligible, key=lambda p: (p["division"], p["dept"], p["name"])):
        roster.setdefault(person["profile_url"], person)
    roster = list(roster.values())
    with open("roster_all.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dept", "division", "name", "rank", "title", "profile_url"])
        writer.writeheader()
        writer.writerows(roster)

    print(f"{len(roster)} eligible faculty in {len({p['dept'] for p in roster})} departments")
    if unclassified:
        print("UNCLASSIFIED units (excluded, please review):", dict(unclassified))


if __name__ == "__main__":
    main()
