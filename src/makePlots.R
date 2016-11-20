setwd("~/af_aad_model/trunk/out/")

library(stringr)
library(ggplot2)
library(plyr)
library(scales)

files <- list.files(pattern = "simData")

df <- NA

for (file in files){
  smys = str_extract(file, "=(.*)S")
  smys = as.numeric(substring(smys, 2, nchar(smys) - 1))
  df.tmp <- read.csv(file, stringsAsFactors = F)
  df.tmp$smys <- smys
  df <- rbind(df, df.tmp)
}

df1 <- ddply(df, c("Grade", "Level", "smys"), function(x){
  return(data.frame(mu = mean(x$fillRate)))
})
