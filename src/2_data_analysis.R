#!/usr/bin/env Rscript

# DOCUMENTATION ------------------------------------------------------------------------------------------------------------------------------------------------
# Author: Kevin Maggi
# Email: kevin.maggi@stud.unifi.it / kevin.maggi@edu.unifi.it

# This script analyzes data resulting from dataset analysis. It performs the following actions:
#  - Trend analysis:
#    - Test for trend (Kendall's Tau test)
#    - Plot Technical Debt and Microservices evolution
#    - Plot Technical Debt trend (LOESS regression)
#    - Potential hotspot identification (order of commit by introduced/payed back Technical Debt)
#  - Seasonality analysis:
#    - Seasonality test (combined test (QS test + Kruskall-Wallis test))
#    - Evolution decomposition (STL decomposition)
#  - Correlation analysis:
#    - Cross-Correlation function between Technical Debt and Microservices
#    - Causality test (Granger test) (if correlated)
#    - Cross-Correlation function between derivatives


# PACKAGES -----------------------------------------------------------------------------------------------------------------------------------------------------
if (!require("readr")) {
  install.packages("readr")
  library(readr)
}
if (!require("Kendall")) {
  install.packages("Kendall")
  library(Kendall)
}
if (!require("ggplot2")) {
  install.packages("ggplot2")
  library(ggplot2)
}
if (!require("scales")) {
  install.packages("scales")
  library(scales)
}
if (!require("dplyr")) {
  install.packages("dplyr")
  library(dplyr)
}
if (!require("lmtest")) {
  install.packages("lmtest")
  library(lmtest)
}
if (!require("seastests")) {
  install.packages("seastests")
  library(seastests)
}
if (!require("VGAM")) {
  install.packages("VGAM")
  library(VGAM)
}
if (!require("tseries")) {
  install.packages("tseries")
  library(tseries)
}
if (!require("vars")) {
  install.packages("vars")
  library(vars)
}


# CONFIGURATIONS -----------------------------------------------------------------------------------------------------------------------------------------------
Sys.setlocale("LC_COLLATE", "C")


# PARAMETERS ---------------------------------------------------------------------------------------------------------------------------------------------------
NO_PAUSE <- TRUE


# MACROS -------------------------------------------------------------------------------------------------------------------------------------------------------
exluded_repos <- list("microrealestate.microrealestate", "dotnet-architecture.eShopOnContainers")
zooms <- read_csv("../data/final/evolution_plots/time/zoom/zoom_definition.csv", show_col_types = FALSE)


# Set up results dataframe
kendall_tau_results <- data.frame(
  REPOSITORY = character(),
  TAU = numeric(),
  P_VALUE = numeric()
)

seasonality_results <- data.frame(
  REPOSITORY = character(),
  SEASONALITY = logical()
)

granger_causality_results <- data.frame(
  REPOSITORY = character(),
  CAUSALITY = logical(),
  P_VALUE = numeric()
)


# analysis
repos_files <- list.files("../data/raw/analysis")
for (repo_file in repos_files) {
  repo_name <- sub("_repo_analysis.csv$", "", repo_file)
  system_name <- paste("S", formatC(which(repo_file == repos_files), width = 2, flag = "0"), sep = "")
  
  # Filter excluded repositories
  if (repo_name %in% exluded_repos) {
    next
  }
  
  print(repo_name)
  
  # Import data analysis
  repo_data <- read_csv(paste("../data/raw/analysis/", repo_file, sep = ""), show_col_types = FALSE)
  repo_data_cleaned <- read_csv(paste("../data/raw/analysis_cleaned/", repo_file, sep = ""), show_col_types = FALSE)
  #View(repo_data)
  #View(repo_data_cleaned)
  
  # Remove failing builds
  repo_data <- repo_data[!is.na(repo_data$SQALE_INDEX), ]
  repo_data_cleaned <- repo_data_cleaned[!is.na(repo_data_cleaned$SQALE_INDEX), ]
  #View(repo_data)
  #View(repo_data_cleaned)
  
  
  
  # TD TREND ANALYSIS ==========================================================================================================================================
  
  ## TD TREND TEST ----
  
  # Kendall's Tau test
  kendall_tau <- MannKendall(repo_data_cleaned$SQALE_INDEX)
  cat("Mann-Kendall test\n\n")
  summary(kendall_tau)
  kendall_tau_results <- rbind(kendall_tau_results, data.frame(REPOSITORY = repo_name, TAU = kendall_tau$tau, P_VALUE = kendall_tau$sl))
  
  
  ## TD/MS PLOT ----
  
  # Convert AUTHOR_DATE column to a Date object
  repo_data_cleaned$AUTHOR_DATE <- as.Date(repo_data_cleaned$AUTHOR_DATE)
  
  life_months <- as.numeric(difftime(tail(repo_data_cleaned$AUTHOR_DATE, n = 1), head(repo_data_cleaned$AUTHOR_DATE, n = 1), units = "weeks")) / 4
  
  # Create plot with time on x-axis
  suppressWarnings({  # necessary warning to get a nice legend
  p <- ggplot(repo_data_cleaned, aes(x = AUTHOR_DATE)) +
    geom_line(aes(y = MICROSERVICES,
                  color = "Number of microservices",
                  linetype = "Number of microservices",
                  shape = "Number of microservices")) +
    geom_line(aes(y = SQALE_INDEX / max(SQALE_INDEX, na.rm = TRUE) * max(MICROSERVICES, na.rm = TRUE),
                  color = "Technical Debt (SQALE index)",
                  linetype = "Technical Debt (SQALE index)",
                  shape = "Technical Debt (SQALE index)")) +
    geom_point(aes(x = ,
                   y = -0.5,
                   color = "Commits",
                   linetype = "Commits",
                   shape = "Commits")) +
    geom_hline(aes(yintercept = -0.5,
                    slope = 0,
                    color = "Commits",
                    linetype = "Commits",
                    shape = "Commits")) +
    scale_color_manual(name = "",
                       breaks = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                       labels = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                       values = c("Commits" = "darkgreen", "Number of microservices" = "orange", "Technical Debt (SQALE index)" = "blue")) +
    scale_linetype_manual(name = "",
                          breaks = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                          labels = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                          values = c("solid", "solid", "solid")) +
    scale_shape_manual(name = "",
                       breaks = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                       labels = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                       values = c(3, NA, NA)) +
    scale_x_date(labels = date_format("%m-%Y"),
                 breaks = seq(min(repo_data_cleaned$AUTHOR_DATE, na.rm = TRUE),
                              max(repo_data_cleaned$AUTHOR_DATE, na.rm = TRUE),
                              by = paste(ceiling(life_months/12), "months")),
                 limits = c(min(repo_data_cleaned$AUTHOR_DATE, na.rm = TRUE),
                            max(repo_data_cleaned$AUTHOR_DATE, na.rm = TRUE))) +
    scale_y_continuous(name = "# microservices",
                       breaks = seq(0, max(repo_data_cleaned$MICROSERVICES, na.rm = TRUE), ceiling(max(repo_data_cleaned$MICROSERVICES, na.rm = TRUE) / 6)),
                       limits = c(-0.5, max(repo_data_cleaned$MICROSERVICES, na.rm = TRUE)),
                       sec.axis = sec_axis(~ . * max(repo_data_cleaned$SQALE_INDEX, na.rm = TRUE) / max(repo_data_cleaned$MICROSERVICES, na.rm = TRUE),
                                           name = "Technical Debt")) +
    labs(x = "Commit date", title = paste("TD & ms evolution (", system_name, ")", sep = "")) +
    theme_gray() +
    theme(text = element_text(family = "sans-serif", size = 18),
          legend.position = "bottom",
          legend.box.background = element_blank(),
          legend.key.size = unit(0.5, "cm"),
          plot.title = element_text(hjust = 0.5),
          axis.text.x = element_text(angle = 45, hjust = 1),
          axis.title.x = element_text(margin = margin(t = 10, r = 0, b = 0, l = 0)),
          axis.title.y = element_text(margin = margin(t = 0, r = 10, b = 0, l = 0)),
          axis.title.y.right = element_text(margin = margin(t = 0, r = 0, b = 0, l = 10)))
  
  # Save plot
  ggsave(paste("../data/final/evolution_plots/time/", repo_name, '.png', sep=""),
         plot = p,
         width = 10,
         height = 5)
  })
  
  # Create a zoom-in for the "hot" period
  if (any(zooms$REPOSITORY == repo_name)) {
    zoom <- zooms[zooms$REPOSITORY == repo_name,]
    
    zoomed_repo_data_cleaned <- repo_data_cleaned[as.numeric(repo_data_cleaned$AUTHOR_DATE) > as.numeric(zoom$FROM) & 
                                                    as.numeric(repo_data_cleaned$AUTHOR_DATE) < as.numeric(zoom$TO),]
    
    # Create plot with two y-axes
    suppressWarnings({  # necessary warning to get a nice legend
      p <- ggplot(zoomed_repo_data_cleaned, aes(x = AUTHOR_DATE)) +
        geom_line(aes(y = MICROSERVICES,
                      color = "Number of microservices",
                      linetype = "Number of microservices",
                      shape = "Number of microservices")) +
        geom_line(aes(y = SQALE_INDEX / max(SQALE_INDEX, na.rm = TRUE) * max(MICROSERVICES, na.rm = TRUE),
                      color = "Technical Debt (SQALE index)",
                      linetype = "Technical Debt (SQALE index)",
                      shape = "Technical Debt (SQALE index)")) +
        geom_point(aes(x = ,
                       y = -0.5,
                       color = "Commits",
                       linetype = "Commits",
                       shape = "Commits")) +
        geom_hline(aes(yintercept = -0.5,
                       slope = 0,
                       color = "Commits",
                       linetype = "Commits",
                       shape = "Commits")) +
        scale_color_manual(name = "",
                           breaks = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                           labels = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                           values = c("Commits" = "darkgreen", "Number of microservices" = "orange", "Technical Debt (SQALE index)" = "blue")) +
        scale_linetype_manual(name = "",
                              breaks = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                              labels = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                              values = c("solid", "solid", "solid")) +
        scale_shape_manual(name = "",
                           breaks = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                           labels = c("Commits", "Number of microservices", "Technical Debt (SQALE index)"),
                           values = c(3, NA, NA)) +
        scale_x_date(labels = date_format("%m-%Y"),
                     breaks = seq(min(zoomed_repo_data_cleaned$AUTHOR_DATE, na.rm = TRUE),
                                  max(zoomed_repo_data_cleaned$AUTHOR_DATE, na.rm = TRUE),
                                  by = paste(1, "months")),
                     limits = c(min(zoomed_repo_data_cleaned$AUTHOR_DATE, na.rm = TRUE),
                                max(zoomed_repo_data_cleaned$AUTHOR_DATE, na.rm = TRUE))) +
        scale_y_continuous(name = "# microservices",
                           breaks = seq(0, 
                                        max(zoomed_repo_data_cleaned$MICROSERVICES, na.rm = TRUE), 
                                        ceiling(max(zoomed_repo_data_cleaned$MICROSERVICES, na.rm = TRUE) / 6)),
                           limits = c(-0.5, max(zoomed_repo_data_cleaned$MICROSERVICES, na.rm = TRUE)),
                           sec.axis = sec_axis(~ . * max(zoomed_repo_data_cleaned$SQALE_INDEX, na.rm = TRUE) / max(zoomed_repo_data_cleaned$MICROSERVICES, na.rm = TRUE),
                                               name = "Technical Debt")) +
        labs(x = "Commit date", title = paste("TD & ms evolution (", system_name, ") - \"hot\" period ", sep = "")) +
        theme_gray() +
        theme(text = element_text(family = "sans-serif", size = 18),
              legend.position = "bottom",
              legend.box.background = element_blank(),
              legend.key.size = unit(0.5, "cm"),
              plot.title = element_text(hjust = 0.5),
              axis.text.x = element_text(angle = 45, hjust = 1),
              axis.title.x = element_text(margin = margin(t = 10, r = 0, b = 0, l = 0)),
              axis.title.y = element_text(margin = margin(t = 0, r = 10, b = 0, l = 0)),
              axis.title.y.right = element_text(margin = margin(t = 0, r = 0, b = 0, l = 10)))
      
      # Save plot
      ggsave(paste("../data/final/evolution_plots/time/zoom/", repo_name, '.png', sep=""),
             plot = p,
             width = 10,
             height = 5)
    })
  }
  
  # Create plot with commit on x-axis
  suppressWarnings({  # necessary warning to get a nice legend
    p <- ggplot(repo_data_cleaned, aes(x = 1:nrow(repo_data_cleaned))) +
      geom_line(aes(y = MICROSERVICES,
                    color = "Number of microservices")) +
      geom_line(aes(y = SQALE_INDEX / max(SQALE_INDEX, na.rm = TRUE) * max(MICROSERVICES, na.rm = TRUE),
                    color = "Technical Debt (SQALE index)")) +
      scale_color_manual(name = "",
                         breaks = c("Number of microservices", "Technical Debt (SQALE index)"),
                         labels = c("Number of microservices", "Technical Debt (SQALE index)"),
                         values = c("Number of microservices" = "orange", "Technical Debt (SQALE index)" = "blue")) +
      scale_y_continuous(name = "# microservices",
                         breaks = seq(0, max(repo_data_cleaned$MICROSERVICES, na.rm = TRUE), ceiling(max(repo_data_cleaned$MICROSERVICES, na.rm = TRUE) / 6)),
                         limits = c(-0.5, max(repo_data_cleaned$MICROSERVICES, na.rm = TRUE)),
                         sec.axis = sec_axis(~ . * max(repo_data_cleaned$SQALE_INDEX, na.rm = TRUE) / max(repo_data_cleaned$MICROSERVICES, na.rm = TRUE),
                                             name = "Technical Debt")) +
      labs(x = "Commit", title = paste("TD & ms evolution (", system_name, ")", sep = "")) +
      theme_gray() +
      theme(text = element_text(family = "sans-serif", size = 18),
            legend.position = "bottom",
            legend.box.background = element_blank(),
            legend.key.size = unit(0.5, "cm"),
            plot.title = element_text(hjust = 0.5),
            axis.title.x = element_text(margin = margin(t = 10, r = 0, b = 0, l = 0)),
            axis.title.y = element_text(margin = margin(t = 0, r = 10, b = 0, l = 0)),
            axis.title.y.right = element_text(margin = margin(t = 0, r = 0, b = 0, l = 10)))
    
    # Save plot
    ggsave(paste("../data/final/evolution_plots/commit/", repo_name, '.png', sep=""),
           plot = p,
           width = 10,
           height = 5)
  })
  
  
  ## INTERPOLATE TD ----
  
  # Keep only the last commit of a day
  repo_data_daily_commit <- repo_data_cleaned %>%
    group_by(AUTHOR_DATE) %>%
    slice(n())
  repo_data_daily_commit <- repo_data_daily_commit[,c("AUTHOR_DATE", "SQALE_INDEX")]
  #View(repo_data_daily_commit)
  
  # Create a daily time-series
  start_date <- head(repo_data_cleaned$AUTHOR_DATE, n = 1)
  end_date <- tail(repo_data_cleaned$AUTHOR_DATE, n = 1)
  date_sequence <- seq(from = start_date, to = end_date, by = "day")
  
  # Create a new dataframe for storing all the daily values
  repo_data_daily_commit_interpolated <- data.frame(matrix(ncol = 3, nrow = 0))
  colnames(repo_data_daily_commit_interpolated) <- c("AUTHOR_DATE", "COMMIT", "SQALE_INDEX")
  
  # Iterate on all day
  for (date in date_sequence) {
    commit_index <- which(repo_data_daily_commit$AUTHOR_DATE == date)
    if (length(commit_index)) {
      # If the day has a commit take that TD
      calculated_TD <- repo_data_daily_commit$SQALE_INDEX[commit_index]
      repo_data_daily_commit_interpolated[nrow(repo_data_daily_commit_interpolated) + 1, ] <- c(date, date, calculated_TD)
    } else {
      # If the day doesn't have a commit interpolate TD
      interpolated_TD <- approx(x = repo_data_daily_commit$AUTHOR_DATE, y = repo_data_daily_commit$SQALE_INDEX, xout = date)$y
      repo_data_daily_commit_interpolated[nrow(repo_data_daily_commit_interpolated) + 1, ] <- c(date, NA, interpolated_TD)
    }
  }
  repo_data_daily_commit_interpolated$AUTHOR_DATE <- as.Date(repo_data_daily_commit_interpolated$AUTHOR_DATE)
  #View(repo_data_daily_commit_interpolated)
  
  
  ## TD TREND SMOOTHING ----
  trend <- stats::loess(repo_data_daily_commit_interpolated$SQALE_INDEX ~ as.numeric(repo_data_daily_commit_interpolated$AUTHOR_DATE), degree = 1)
  
  # Create plot
  suppressWarnings({  # necessary warning to get a nice legend
    p <- ggplot(repo_data_daily_commit_interpolated, aes(x = AUTHOR_DATE)) +
      geom_line(aes(y = SQALE_INDEX), color = "deepskyblue") +
      geom_line(aes(y = trend$fitted), color = "darkblue") +
      geom_point(x = repo_data_daily_commit_interpolated$COMMIT,
                 y = -0.5,
                 color = "darkgreen",
                 shape = 3) +
      geom_hline(yintercept = -0.5,
                 slope = 0,
                 color = "darkgreen") +
      scale_x_date(labels = date_format("%m-%Y"),
                   breaks = seq(min(repo_data_daily_commit_interpolated$AUTHOR_DATE, na.rm = TRUE),
                                max(repo_data_daily_commit_interpolated$AUTHOR_DATE, na.rm = TRUE),
                                by = paste(ceiling(life_months/12), "months")),
                   limits = c(min(repo_data_daily_commit_interpolated$AUTHOR_DATE, na.rm = TRUE),
                              max(repo_data_daily_commit_interpolated$AUTHOR_DATE, na.rm = TRUE))) +
      scale_y_continuous(name = "Technical Debt (SQALE index)",
                         limits = c(-0.5, max(max(trend$fitted, na.rm = TRUE), max(repo_data_daily_commit_interpolated$SQALE_INDEX)))) +
      labs(x = "Date", title = paste("TD trend (", system_name, ")", sep = "")) +
      theme_gray() +
      theme(text = element_text(family = "sans-serif", size = 18),
            legend.position = "none",
            plot.title = element_text(hjust = 0.5),
            axis.text.x = element_text(angle = 45, hjust = 1),
            axis.title.x = element_text(margin = margin(t = 10, r = 0, b = 0, l = 0)),
            axis.title.y = element_text(margin = margin(t = 0, r = 10, b = 0, l = 0)))
    
    # Save plot
    ggsave(paste("../data/final/trend_plots/", repo_name, '.png', sep=""),
           plot = p,
           width = 10,
           height = 5)
  })

  
  
  ## POTENTIAL HOTSPOT IDENTIFICATION ----
  
  # Identify and remove merge commits
  non_merge_commits <- subset(repo_data, !grepl(" ", PARENT))
  #View(non_merge_commits)
  
  non_merge_delta_td_commits <- apply(non_merge_commits, 1, function(commit) {
    if (!is.na(commit["PARENT"])) {
      # Find the parent (it can be also a merge commit)
      parent <- repo_data[repo_data$COMMIT == commit["PARENT"], ]
      
      # Subtract the parent's TD to get the new TD introduced
      commit["SQALE_INDEX"] <- as.numeric(commit["SQALE_INDEX"]) - as.numeric(parent["SQALE_INDEX"])
    }
    return(commit)
  })
  non_merge_delta_td_commits <- as.data.frame(t(non_merge_delta_td_commits))
  #View(non_merge_delta_td_commits)
  
  # Order commits by absolute TD delta introduced
  non_merge_delta_td_commits <- non_merge_delta_td_commits[order(-abs(as.numeric(non_merge_delta_td_commits$SQALE_INDEX))), ]
  
  # Write ordered commits to CSV file
  write.csv(non_merge_delta_td_commits,
            file = paste("../data/final/hotspots/", repo_name, '.csv', sep=""),
            row.names = FALSE)

  

  # SEASONALITY ANALYSIS =======================================================================================================================================
  
  if (life_months >= 24) {  # Tests and STL works only if there is at least two periods, so discard repositories that have a shorter life
    
    ## TEST FOR SEASONALITY ----
    seasonality <- isSeasonal(diff(repo_data_daily_commit_interpolated$SQALE_INDEX), test = "combined", freq = 365)
    cat(paste("\nSeasonality test:", seasonality, "\n\n"))
    seasonality_results <- rbind(seasonality_results, data.frame(REPO = repo_name, SEASONALITY = seasonality))
    
    
    ## STL DECOMPOSITION ----
    if (seasonality) {
      # Create time-series of TD
      TD_ts <- ts(repo_data_daily_commit_interpolated$SQALE_INDEX, frequency = 365)
      
      # Decompose with STL
      TD_STL <- stl(TD_ts, s.window = "periodic")
      
      # Extract the seasonal, trend and remainder components
      TD_seasonal <- TD_STL$time.series[, "seasonal"]
      TD_trend <- TD_STL$time.series[, "trend"]
      TD_irregular <- TD_STL$time.series[, "remainder"]
     
      # Create a dataframe with components
      TD_decomposed <- data.frame(
        AUTHOR_DATE = rep(repo_data_daily_commit_interpolated$AUTHOR_DATE, 3),
        Component = factor(rep(c("Trend", "Seasonal", "Irregular"), each = length(TD_ts)), levels = c("Trend", "Seasonal", "Irregular")),
        Value = c(TD_trend, TD_seasonal, TD_irregular)
      )
    
      # Create a composed plot showing all the components
      p <- ggplot(TD_decomposed, aes(x = AUTHOR_DATE, y = Value)) +
        geom_line(color = "blue") +
        facet_wrap(~ Component, ncol = 3) +
        scale_x_date(labels = date_format("%m-%Y"), 
                     breaks = seq(min(repo_data_daily_commit_interpolated$AUTHOR_DATE),
                                  max(repo_data_daily_commit_interpolated$AUTHOR_DATE),
                                  by = paste(ceiling(life_months/9), "months")),
                     limits = c(min(repo_data_daily_commit_interpolated$AUTHOR_DATE, na.rm = TRUE),
                                max(repo_data_daily_commit_interpolated$AUTHOR_DATE, na.rm = TRUE))) +
        scale_y_continuous(name = "Technical Debt (SQALE index)") +
        labs(x = "Date", title = paste("TD evolution decomposition (", system_name, ")", sep = "")) +
        theme_gray() +
        theme(text=element_text(family="sans-serif", size = 18),
              plot.title = element_text(hjust = 0.5),
              axis.text.x = element_text(angle = 45, hjust = 1),
              axis.title.x = element_text(margin = margin(t = 10, r = 0, b = 0, l = 0)),
              axis.title.y = element_text(margin = margin(t = 0, r = 10, b = 0, l = 0)))
    
      # Save plot
      ggsave(paste("../data/final/stl_plots/", repo_name, '.png', sep=""),
             plot = p,
             width = 10,
             height = 5)
      
    }
  }

  
  
  # CORRELATION ANALYSIS =======================================================================================================================================
  
  ## CORRELATION TD/MS ----
  
  # Get z-scores (standardization)
  ms <- scale(repo_data_cleaned$MICROSERVICES)[,1]
  td <- scale(repo_data_cleaned$SQALE_INDEX)[,1]
  
  # Test for stationarity with Augmented Dickey-Fuller test
  if (adf.test(ms)$p.value > 0.05 | adf.test(td)$p.value > 0.05) {
    # Differentiate (to make stationary)
    ms <- diff(ms)
    td <- diff(td)
  }
  
  # Calculate Cross-Correlation Function on data
  cross_corr_1st <- ccf(ms, td, pl = TRUE)
  cross_corr_df <- with(cross_corr_1st, data.frame(lag, acf))
  
  conf_int <- qnorm((1 - 0.95)/2)/sqrt(cross_corr_1st$n.used)
  
  # Plot results
  p <- ggplot(data = cross_corr_df, mapping = aes(x = lag, y = acf)) +
    geom_hline(aes(yintercept = 0)) +
    geom_segment(mapping = aes(xend = lag, yend = 0)) +
    geom_hline(aes(yintercept = conf_int), linetype = "dashed", color = 'darkblue') + 
    geom_hline(aes(yintercept = -conf_int), linetype = "dashed", color = 'darkblue') +
    labs(x = "Lag", y = "CCF", title = paste("TD & ms\n Cross-Correlation (", system_name, ")", sep = "")) +
    theme_gray() +
    theme(text = element_text(family = "sans-serif", size = 18),
          plot.title = element_text(hjust = 0.5),
          axis.title.x = element_text(margin = margin(t = 10, r = 0, b = 0, l = 0)),
          axis.title.y = element_text(margin = margin(t = 0, r = 10, b = 0, l = 0)),)
  
  # Save plot
  ggsave(paste("../data/final/1st_correlation_plots/", repo_name, '.png', sep=""),
         plot = p,
         width = 4.5,
         height = 3.5)
  
  ### CAUSALITY ---- 
  
  # If ms leads td, test causality
  if (any(abs(cross_corr_1st$acf[1:ceiling(length(cross_corr_1st$lag)/2)]) > abs(conf_int))) {
    # Estimate an appropriate lag order using Akaike Information Criteria
    var_select <- VARselect(cbind(td, ms), lag.max = abs(cross_corr_1st$lag[1]), type = "const")
    lag_order <- var_select$selection["AIC(n)"]
    
    # Granger causality test
    granger_test <- grangertest(td ~ ms, order = lag_order)
    print(granger_test)
    granger_causality_results <- rbind(granger_causality_results, data.frame(REPO = repo_name, 
                                                                             CAUSALITY = ifelse(tail(granger_test, n = 1)$`Pr(>F)` < 0.05, TRUE, FALSE), 
                                                                             P_VALUE = tail(granger_test, n = 1)$`Pr(>F)`))
  }
  
  
  ## CORRELATION TD'/MS ----

  # Get derivative
  td <- diff(td)
  
  # Test for stationarity with Augmented Dickey-Fuller test
  if (adf.test(td)$p.value > 0.05) {
    # Differentiate (to make stationary)
    td <- diff(td)
  }

  # Calculate Cross-Correlation Function on data
  cross_corr_2nd <- ccf(ms, td, pl = TRUE)
  cross_corr_df <- with(cross_corr_2nd, data.frame(lag, acf))

  conf_int <- qnorm((1 - 0.95)/2)/sqrt(cross_corr_2nd$n.used)

  # Plot results
  p <- ggplot(data = cross_corr_df, mapping = aes(x = lag, y = acf)) +
    geom_hline(aes(yintercept = 0)) +
    geom_segment(mapping = aes(xend = lag, yend = 0)) +
    geom_hline(aes(yintercept = conf_int), linetype = "dashed", color = 'darkblue') +
    geom_hline(aes(yintercept = -conf_int), linetype = "dashed", color = 'darkblue') +
    labs(x = "Lag", y = "CCF", title = paste("TD' & ms\n Cross-Correlation (", system_name, ")", sep = "")) +
    theme_gray() +
    theme(text = element_text(family = "sans-serif", size = 18),
          plot.title = element_text(hjust = 0.5),
          axis.title.x = element_text(margin = margin(t = 10, r = 0, b = 0, l = 0)),
          axis.title.y = element_text(margin = margin(t = 0, r = 10, b = 0, l = 0)),)

  # Save plot
  ggsave(paste("../data/final/2nd_correlation_plots/", repo_name, '.png', sep=""),
         plot = p,
         width = 4.5,
         height = 3.5)
  
  
  
  # Pause script if pause has been set
  if (!NO_PAUSE) {
    input <- readline(prompt = "Press [Enter] to go to the next repository or [Esc] to exit\n")
    if (input == "\033") {
      print("You pressed [Esc]\n")
      break
    }
  }
}


# Write results of tests
write_csv(kendall_tau_results, "../data/final/trend_results.csv")
write_csv(seasonality_results, "../data/final/seasonality_results.csv")
write_csv(granger_causality_results, "../data/final/causality_results.csv")
