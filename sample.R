# STA 322 Project 1 -- stratified simple random sample of Trinity tenure-track faculty.
# Strata = the 27 Trinity departments (primary appointment). Proportional allocation
# targeting n = 120, with at least 2 per department (needed for within-stratum variance).
# Input:  roster_all.csv (eligible frame, from build_frame.py)
# Output: sample.csv

library(dplyr)
library(readr)

frame <- read_csv("roster_all.csv", show_col_types = FALSE) |>
  arrange(dept, profile_url)                 # fixed order so the seed is reproducible

n_target <- 120
N <- nrow(frame)

alloc <- frame |>
  count(division, dept, name = "M_h") |>
  mutate(n_h = pmin(M_h, pmax(2, round(n_target * M_h / N))))

set.seed(21)
smp <- frame |>
  inner_join(alloc, by = c("division", "dept")) |>
  group_by(dept) |>
  group_modify(~ .x[sample(nrow(.x), .x$n_h[1]), ]) |>
  ungroup() |>
  mutate(pi = n_h / M_h, w = 1 / pi) |>
  select(division, dept, M_h, n_h, pi, w, name, rank, title, profile_url)

write_csv(smp, "sample.csv")

cat("Frame size N =", N, " sample size n =", nrow(smp), " sum of weights =", sum(smp$w), "\n")
print(as.data.frame(alloc), row.names = FALSE)
