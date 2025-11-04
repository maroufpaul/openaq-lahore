library(readr) 
library(dplyr)

in_csv  <- "C:/Users/Lan Zhang/Downloads/lahore_pop_1km.csv"     
out_mat <- "C:/Users/Lan Zhang/Downloads/lahore_grid_52x52_matrix.csv"
out_tbl <- "C:/Users/Lan Zhang/Downloads/lahore_grid_52x52_table.csv"  

df <- read_csv(in_csv, col_types = "ddd")  # lon, lat, pop

# Build 52×52 bins over the data’s bbox 
nx <- 52; ny <- 52
lon_breaks <- seq(min(df$lon), max(df$lon), length.out = nx + 1)
lat_breaks <- seq(min(df$lat), max(df$lat), length.out = ny + 1)

# Grid cell 
df <- df %>%
  mutate(
    col = cut(lon, breaks = lon_breaks, include.lowest = TRUE, labels = FALSE),
    row = cut(lat, breaks = lat_breaks, include.lowest = TRUE, labels = FALSE)
  ) %>%
  filter(!is.na(row), !is.na(col))

# Sum population per cell
agg <- df %>%
  group_by(row, col) %>%
  summarise(pop_sum = sum(pop_sum, na.rm = TRUE), .groups = "drop")

# Build 52×52 matrix 
mat <- matrix(0, nrow = ny, ncol = nx)
idx <- cbind(agg$row, agg$col)
mat[idx] <- agg$pop_sum

# Make row 1 be the north/top of the map 
mat <- mat[ny:1, , drop = FALSE]

# Save results
write.table(mat, out_mat, sep = ",", row.names = FALSE, col.names = FALSE)
write.csv(agg, out_tbl, row.names = FALSE)
image(t(mat[nrow(mat):1, ]), axes = FALSE, main = "Lahore population (52×52)")
