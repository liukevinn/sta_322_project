# Step 5: draw the stratified random sample.
# Each of the 27 departments is a stratum. We take a simple random sample in each one,
# sized in proportion to the department (target n = 120), with at least 2 per department
# so the within-department variance can be estimated.
# Reads roster_all.csv, writes sample.csv.

library(dplyr)
library(readr)

frame <- read_csv("roster_all.csv", show_col_types = FALSE) |>
  arrange(dept, profile_url)        # fixed row order, so the seed always gives the same sample
N <- nrow(frame)

allocation <- frame |>
  count(division, dept, name = "M_h") |>
  mutate(n_h = pmin(M_h, pmax(2, round(120 * M_h / N))))

set.seed(21)
sampled <- frame |>
  inner_join(allocation, by = c("division", "dept")) |>
  group_by(dept) |>
  group_modify(~ .x[sample(nrow(.x), .x$n_h[1]), ]) |>
  ungroup() |>
  mutate(pi = n_h / M_h, w = 1 / pi) |>
  select(name, dept, M_h, n_h, pi, w, profile_url)   # profile_url is used to collect the data

write_csv(sampled, "sample.csv")

cat("Frame size N =", N, " sample size n =", nrow(sampled), " sum of weights =", sum(sampled$w), "\n")
print(as.data.frame(allocation), row.names = FALSE)
