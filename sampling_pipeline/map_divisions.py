"""Step 4 (documentation only): label every entry in the search page's Department filter.

Each entry is marked as a Trinity department or program (with its division), an affiliated
institute or center, or a non-Trinity unit. The divisions come from Trinity's own pages
(read 2026-10-08):
  https://trinity.duke.edu/arts-humanities
  https://trinity.duke.edu/natural-sciences
  https://trinity.duke.edu/social-sciences

Reads:  scholars_department_facet.tsv, roster_all.csv
Writes: divisions.csv
"""
import csv
from collections import Counter

from build_frame import DIVISION, HUM, NAT, SOC

DEPARTMENT_NOTES = {
    "Literature": "listed by Trinity under Departments & Programs",
    "Psychology & Neuroscience": "CROSS-LISTED: Trinity lists it under BOTH Natural and Social Sciences",
}

# Trinity programs that are not departments: (division, unit type, note).
PROGRAMS = {
    "Dance Program": (HUM, "program", ""),
    "Writing and Rhetoric Program": (HUM, "program",
                                     "Trinity's page lists 'Thompson Writing Program'; assumed the same unit"),
    "Cinematic Arts": (HUM, "specialized program", ""),
    "Computational Media, Arts & Cultures": (HUM, "specialized program", ""),
    "Information Science + Studies": (HUM, "specialized program", ""),
    "Masters of Fine Arts in Experimental and Documentary Arts": (HUM, "specialized program", ""),
    "Air Force Reserve Officer Training Corps (ROTC)": (NAT, "ROTC program", ""),
    "Army Reserve Officer Training Corps (ROTC)": (NAT, "ROTC program", ""),
    "Education": (SOC, "program", "Program in Education; Scholars also lists 'Education Program'"),
    "Education Program": (SOC, "program", "duplicate label of Education"),
    "International Comparative Studies": (SOC, "program", ""),
    "Linguistics": (SOC, "program", ""),
    "Markets & Management Studies": (SOC, "specialized program", ""),
}

# Listed on a division page as an affiliated institute or center: their division(s).
AFFILIATED = {
    "Asian Pacific Studies Institute": HUM, "John Hope Franklin Humanities Institute": HUM,
    "Kenan Institute for Ethics": f"{HUM}; {SOC}", "Sperling Center for Jewish Studies": HUM,
    "Center for Documentary Studies": HUM,
    "Duke Global Health Institute": f"{NAT}; {SOC}", "Duke Institute for Brain Sciences": NAT,
    "Duke Population Research Institute": f"{NAT}; {SOC}",
    "Duke Population Research Center": SOC, "Duke Network Analysis Center": SOC,
    "Center for Population Health & Aging": SOC, "Social Science Research Institute": SOC,
    "Nicholas School of the Environment": NAT, "Sanford School of Public Policy": SOC,
}


def classify(unit):
    """(division, unit type, note) for one entry of the Department filter."""
    if unit in DIVISION:
        return DIVISION[unit], "department", DEPARTMENT_NOTES.get(unit, "")
    if unit in PROGRAMS:
        return PROGRAMS[unit]
    if unit in AFFILIATED:
        return AFFILIATED[unit], "affiliated institute/center", "not a department"
    return "", "non-Trinity unit", "secondary appointments of Trinity faculty"


facet = list(csv.DictReader(open("scholars_department_facet.tsv"), delimiter="\t"))
eligible_count = Counter(row["dept"] for row in csv.DictReader(open("roster_all.csv")))

with open("divisions.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["department", "n_faculty_search", "M_i_eligible", "division", "unit_type", "note"])
    for row in facet:
        unit = row["department"]
        writer.writerow([unit, row["n_faculty"], eligible_count[unit], *classify(unit)])

print(Counter(classify(row["department"])[1] for row in facet))
