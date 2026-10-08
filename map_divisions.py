"""Assign every entry in the Scholars search page's Department filter (Trinity + Faculty)
to a Trinity division, using Trinity College's own division pages:
  https://trinity.duke.edu/arts-humanities
  https://trinity.duke.edu/natural-sciences
  https://trinity.duke.edu/social-sciences
(read 2026-10-08).

Inputs:  scholars_department_facet.tsv, roster_all.csv
Output:  divisions.csv  department, n_faculty_search, M_i_eligible, division, unit_type, note
"""
import csv
from collections import Counter

H, N, S = "Humanities", "Natural Sciences", "Social Sciences"

# (division, unit_type, note); names are as they appear in Scholars.
TRINITY = {
    # Arts & Humanities: "Departments & Programs"
    "Art, Art History & Visual Studies": (H, "department", ""),
    "Asian & Middle Eastern Studies": (H, "department", ""),
    "Classical Studies": (H, "department", ""),
    "Dance Program": (H, "program", ""),
    "English": (H, "department", ""),
    "German Studies": (H, "department", ""),
    "Literature": (H, "department", "listed by Trinity under Departments & Programs"),
    "Music": (H, "department", ""),
    "Philosophy": (H, "department", ""),
    "Religious Studies": (H, "department", ""),
    "Romance Studies": (H, "department", ""),
    "Slavic & Eurasian Studies": (H, "department", ""),
    "Theater Studies": (H, "department", ""),
    "Writing and Rhetoric Program": (H, "program",
                                     "Trinity's page lists 'Thompson Writing Program'; assumed the same unit"),
    # Arts & Humanities: "Specialized Programs & Curricula"
    "Cinematic Arts": (H, "specialized program", ""),
    "Computational Media, Arts & Cultures": (H, "specialized program", ""),
    "Information Science + Studies": (H, "specialized program", ""),
    "Masters of Fine Arts in Experimental and Documentary Arts": (H, "specialized program", ""),
    # Natural Sciences: "Departments & Programs"
    "Biology": (N, "department", ""),
    "Chemistry": (N, "department", ""),
    "Computer Science": (N, "department", ""),
    "Evolutionary Anthropology": (N, "department", ""),
    "Mathematics": (N, "department", ""),
    "Physics": (N, "department", ""),
    "Psychology & Neuroscience": (N, "department",
                                  "CROSS-LISTED: Trinity lists it under BOTH Natural and Social Sciences"),
    "Statistical Science": (N, "department", ""),
    # Natural Sciences: "ROTC Programs"
    "Air Force Reserve Officer Training Corps (ROTC)": (N, "ROTC program", ""),
    "Army Reserve Officer Training Corps (ROTC)": (N, "ROTC program", ""),
    # Social Sciences: "Departments & Programs"
    "African & African American Studies": (S, "department", ""),
    "Cultural Anthropology": (S, "department", ""),
    "Economics": (S, "department", ""),
    "Education": (S, "program", "Program in Education; Scholars also lists 'Education Program'"),
    "Education Program": (S, "program", "duplicate label of Education"),
    "Gender, Sexuality & Feminist Studies": (S, "department", ""),
    "History": (S, "department", ""),
    "International Comparative Studies": (S, "program", ""),
    "Linguistics": (S, "program", ""),
    "Political Science": (S, "department", ""),
    "Sociology": (S, "department", ""),
    # Social Sciences: "Specialized Programs"
    "Markets & Management Studies": (S, "specialized program", ""),
}

# Listed on a division page as an affiliated institute/center (not a Trinity department).
AFFILIATED = {
    "Asian Pacific Studies Institute": H, "John Hope Franklin Humanities Institute": H,
    "Kenan Institute for Ethics": f"{H}; {S}", "Sperling Center for Jewish Studies": H,
    "Center for Documentary Studies": H,
    "Duke Global Health Institute": f"{N}; {S}", "Duke Institute for Brain Sciences": N,
    "Duke Population Research Institute": f"{N}; {S}",
    "Duke Population Research Center": S, "Duke Network Analysis Center": S,
    "Center for Population Health & Aging": S, "Social Science Research Institute": S,
    "Nicholas School of the Environment": N, "Sanford School of Public Policy": S,
}

facet = list(csv.DictReader(open("scholars_department_facet.tsv"), delimiter="\t"))
m_i = Counter(r["dept"] for r in csv.DictReader(open("roster_all.csv")))

with open("divisions.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["department", "n_faculty_search", "M_i_eligible", "division", "unit_type", "note"])
    for r in facet:
        d = r["department"]
        if d in TRINITY:
            div, typ, note = TRINITY[d]
        elif d in AFFILIATED:
            div, typ, note = AFFILIATED[d], "affiliated institute/center", "not a department"
        else:
            div, typ, note = "", "non-Trinity unit", "secondary appointments of Trinity faculty"
        w.writerow([d, r["n_faculty"], m_i.get(d, 0), div, typ, note])

print(Counter(TRINITY[d][1] if d in TRINITY else "affiliated" if d in AFFILIATED else "non-Trinity"
              for d in (r["department"] for r in facet)))
