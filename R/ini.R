rm(list = ls())

# https://github.com/dvdscripter/ini/blob/master/R/ini.R


# file.ini.obj <- file(path.ini, encoding = your.encoding)
# #close(file.ini.obj)

trim <- function(x) {
    sub('^\\s*(.*?)\\s*$', '\\1', x)
}

helper_guess_line_status <- function(line.str) {
    sectionREGEXP <- '^\\s*\\[\\s*(.+?)\\s*]'
    # match section and capture section name
    
    keyValueREGEXP <- '^\\s*[^=]+=?.?'
    # match "key = value" pattern
    
    ignoreREGEXP <- '^\\s*[;#]'
    # match lines with ; or # at start
    if (nchar(line.str) < 1 ||
        grepl(ignoreREGEXP, line.str)) {
        return("ignore")
    }
    if (grepl(sectionREGEXP, line.str)) {
        return("section")
    }
    if (grepl(keyValueREGEXP, line.str)) {
        return("key")
    }
    
} # end of helper_guess_line_status

extract_section <- function(line.ini.section) {
    sub("\\[(.+)\\]", "\\1", line.ini.section)
} # end of extract_section

extract_key <- function(line.ini) {
    tmp <- sub("=.*", "", line.ini)
    trim(tmp)
} # end of extract_key

extract_value <- function(line.ini) {
    tmp <- sub(".*=", "", line.ini)
    trim(tmp)
} # end of extract_value



Load_INI_RAW <- function(path.ini) {
    lines.ini <- readLines(path.ini)
    
    try(if (length(lines.ini) < 1) {
        #" exit program
        stop("file is empty...")
    })
    
    section.name <- ""
    res <- list()
    for (li in seq_along(lines.ini))
    {
        line.this <- trim(lines.ini[li])
        status.line <- helper_guess_line_status(line.this)
        
        key.this <- NULL
        value.this <- NULL
        if (status.line == "ignore") {
            next
        }
        
        if (status.line == "section") {
            # print(extract_section(line.this))
            section.name <- extract_section(line.this)
            res[[section.name]] <- list()
        }
        if (status.line == "key") {
            # print(c(extract_key(line.this), extract_value(line.this)))
            key.this <- extract_key(line.this)
            value.this <- extract_value(line.this)
            res[[section.name]][[key.this]] <- value.this
        }
        # print(paste(section.name, key.this, value.this, sep = " --> "))
    }
    return(res)
}


lst2table <- function(lst.from.ini) {
    k_section <- NULL
    k_key <- NULL
    val <- NULL
    for (section in names(lst.from.ini)) {
        this.section <- lst.from.ini[[section]]
        for (key in names(this.section)) {
            k_section <- c(k_section, section)
            k_key <- c(k_key, key)
            val <- c(val, this.section[[key]])
        }
    }
    
    uid <- paste(k_section , ":", k_key, sep = "")
    data.frame(
        "uid" = uid,
        "section" = k_section,
        "key" = k_key,
        "value" = val,
        stringsAsFactors = F
    )
} # end of lst2table

regexpINFER <- "\\$\\{.+?\\:.+?\\}"

helper_detect_infer <- function(chr.val) {
    grepl(regexpINFER, chr.val)
}

helper_extract_infer <- function(chr.val) {
    raw.lst <- regmatches(chr.val, gregexpr(regexpINFER, chr.val))
    sapply(raw.lst, function(x) {
        sub("\\$\\{(.+?\\:.+?)\\}", "\\1", x)
    })
}


make_adjace_list_from_table <- function(tab.ini) {
    stopifnot(all(c("uid", "value", "section", "key") %in% names(tab.ini)))
    res <- list()
    for (index.row in seq_along(tab.ini$uid)) {
        val.this <- tab.ini$value[index.row]
        if (helper_detect_infer(val.this)) {
            uid.this <- tab.ini$uid[index.row]
            res[[uid.this]] <- helper_extract_infer(val.this)
        }
        
    }
    return(res)
}
#' detect whether there is a cycle in this ini file
DetectCircleInAdjacentList <- function(al.ini) {
    
    visited.lst <- list()
    for  (x in names(al.ini)) {
        visited.lst[[x]] <- 0 
    }
    
    graph.al <- al.ini
    has_circ <- F
    detect_dfs <- function(uid, visited.lst) {
        visited.lst[[uid]] <- -1
        while (length(graph.al[[uid]]) > 0) {
            
            neighbor.this <- graph.al[[uid]][1]
            graph.al[[uid]] <- graph.al[[uid]][-1]
            
            if (visited.lst[[neighbor.this]] == 0) {
                detect_dfs(neighbor.this, visited.lst)
                visited.lst[[neighbor.this]] = 1
                
            } else {
                if (visited.lst[[neighbor.this]] == -1) {
                    #                print("has_Circ")
                    has_circ <<- T
                }
            }
            
        }
    }
    
    detect_dfs(names(graph.al)[1], visited.lst)
    return(has_circ)
}




# test --------------------------------------------------------------------

library(magrittr)

"./test/minimal.cfg" %>% Load_INI_RAW() %>% lst2table() %>% make_adjace_list_from_table() %>% DetectCircleInAdjacentList()


# path.ini <- "./test/minimal.functional.cfg"
path.ini <- "./test/minimal.cfg"
res.raw <- Load_INI_RAW(path.ini) 
tab.raw <- lst2table(res.raw)

# sapply(tab.raw$value[1], helper_extract_infer)
al.ini <- make_adjace_list_from_table(tab.raw)
