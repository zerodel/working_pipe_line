#! /usr/bin/env Rscript

# description of this script ----------------------------------------------
#' FUNCTIONALITY

#' USAGE

#' ARGUMENTS  


# check dependency  and try install missing package -----------------------
BasicInstall <- function(p) {
    install.packages(p, repos = "http://cran.r-project.org")
}

BioconductorInstall <- function(p) {
    source("https://bioconductor.org/biocLite.R")
    biocLite(p)
}

CheckDependencies <- function(package_list, func_install=BasicInstall) {
    for (p in package_list) {
        if (!suppressWarnings(suppressMessages(require(
            p,
            character.only = TRUE,
            quietly = TRUE,
            warn.conflicts = FALSE
        )))) {
            #' try use cran as package source.
            func_install(p)
            suppressWarnings(suppressMessages(library(
                p,
                character.only = TRUE,
                quietly = TRUE,
                warn.conflicts = FALSE
            )))
        }
    }
}


CheckDependencies(c("tidyverse", "optparse", "data.table"))
CheckDependencies(c("DESeq2", "GenomicFeatures"), func_install = BioconductorInstall)


# clean enviroment and load packages --------------------------------------------------------
rm(list = base::ls())
library(tidyverse)

# ---------------------------------------------------------


LoadQuant <- function(path, sample_name = NULL) {
    if (require(data.table)) {
        x <- data.table::fread(path, stringsAsFactors = F)
    } else{
        x <- read.table(path, stringsAsFactors = F)
    }
    
    if (!is.null(sample_name)) {
        x$sample <- sample_name
    }
    if (require(tibble)) {
        x %>% tibble::as_tibble()
    }
}


SUB_PATH_FA <- "final.fa"
SUB_PATH_GTF <- "final.gtf"
SUB_PATH_QUANT <- "profile_result/quant.sf"
SUB_PATH_QUANT_GENE <- "profile_result/quant.gene.sf"

Serial_Sample_Sub_Path <- function(dir.quant, suffix_path = SUB_PATH_QUANT) {
    safe.dir <- sub("\\/$", "", dir.quant)
    samples.raw <-
        list.dirs(dir.quant, full.names = F, recursive = F)
    path.sf <-
        paste(safe.dir, "/", samples.raw, suffix_path, sep = "")
    res <- list()
    for (x in seq_along(samples.raw)) {
        res[[samples.raw[x]]] <- path.sf[x]
    }
    
    return(res)
}

