library(terra)

tif <- "C:/Users/Lan Zhang/Downloads/pak_ppp_2020.tif"

r <- rast(tif)

# Clip to a Lahore bounding
lahore_bbox <- ext(74.10, 74.60, 31.25, 31.65)
r_lahore <- crop(r, lahore_bbox)

# Save GeoTIFF
writeRaster(r_lahore, "C:/Users/Lan Zhang/Downloads/pop_2020_lahore_bbox.tif", overwrite=TRUE)

r1km <- aggregate(r_lahore, fact=10, fun="sum", na.rm=TRUE)
df1  <- as.data.frame(r1km, xy=TRUE, na.rm=TRUE)
names(df1) <- c("lon","lat","pop_sum")
write.csv(df1, "C:/Users/Lan Zhang/Downloads/lahore_pop_1km.csv", row.names=FALSE)