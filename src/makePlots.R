setwd("~/Science Projects/af_aad_model/trunk/out/")

library(stringr)
library(ggplot2)
library(plyr)
library(scales)
library(ggthemes)

files <- list.files(pattern = "simData")

df <- NA

for (file in files){
  smys = str_extract(file, "=(.*)S")
  smys = as.numeric(substring(smys, 2, nchar(smys) - 1))
  df.tmp <- read.csv(file, stringsAsFactors = F)
  df.tmp$smys <- smys
  df <- rbind(df, df.tmp)
}

df <- subset(df, df$Level %in% c("DOCTORATE", "AWARDED MASTERS DEGREE"))
df <- subset(df, df$Grade != "COL")

df1 <- ddply(df, c("smys", "Grade"), function(x){
  return(data.frame(mu = mean(x$fillRate, na.rm = T)))
})

ggplot(df1, aes(x = smys, y = mu, color = Grade)) + 
  geom_point(size = 3) + 
  scale_color_tableau()