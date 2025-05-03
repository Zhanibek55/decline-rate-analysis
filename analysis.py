import polars as pl
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from utils import load_data, calculate_decline_rate, safe_to_pandas
from logger import logger, safe_log

# Loading test data
try:
    prod_path = r"c:\Users\znugm\Documents\KMGE2025\Темп падения\test_data\prod_data.csv"
    events_path = r"c:\Users\znugm\Documents\KMGE2025\Темп падения\test_data\events_data.csv"
    
    print("Loading production data from:", prod_path)
    prod_df = pl.read_csv(prod_path)
    print("Number of rows in production data:", len(prod_df))
    print("Columns in production data:", prod_df.columns)
    print("Sample production data:")
    print(prod_df.head(5))
    
    print("\nLoading events data from:", events_path)
    events_df = pl.read_csv(events_path)
    print("Number of rows in events data:", len(events_df))
    print("Columns in events data:", events_df.columns)
    print("Sample events data:")
    print(events_df.head(5))
    
    # Analyzing production data
    print("\nProduction data analysis:")
    print("Unique wells:", prod_df["well_id"].unique().to_list())
    print("Number of wells:", len(prod_df["well_id"].unique()))
    print("Unique horizons:", prod_df["horizon"].unique().to_list())
    print("Unique dates:", prod_df["date"].unique().to_list())
    print("Minimum date:", min(prod_df["date"].unique()))
    print("Maximum date:", max(prod_df["date"].unique()))
    
    # Checking data for decline rate calculation
    start_date = "2023/01/01"
    end_date = "2024/01/01"
    print(f"\nCalculating decline rate for period: {start_date} - {end_date}")
    
    # Checking date filtering
    filtered_df = prod_df.filter(
        (pl.col("date") >= start_date) & 
        (pl.col("date") <= end_date)
    )
    print("Number of rows after date filtering:", len(filtered_df))
    
    # Checking grouping by horizon
    group_by_cols = ["horizon"]
    grouped = filtered_df.group_by(["date"] + group_by_cols)
    agg = grouped.agg([
        pl.sum("oil_rate").alias("sum_oil_rate"),
        pl.count("well_id").alias("well_count")
    ])
    print("\nGrouping result by horizon:")
    print(agg.head(5))
    
    # Checking if we have data for two dates (t0 and t1)
    unique_dates = agg["date"].unique().sort()
    print("\nUnique dates after grouping:", unique_dates.to_list())
    
    if len(unique_dates) >= 2:
        t0 = min(unique_dates)
        t1 = max(unique_dates)
        print(f"Start date (t0): {t0}")
        print(f"End date (t1): {t1}")
        
        # Performing decline rate calculation
        print("\nPerforming decline rate calculation:")
        result = calculate_decline_rate(
            prod_df=prod_df,
            events_df=events_df,
            start_date=start_date,
            end_date=end_date,
            group_by_cols=group_by_cols,
            rate_col="oil_rate",
            include_events=False
        )
        
        print("Decline rate calculation result:")
        if len(result) > 0:
            print(result)
        else:
            print("Result is empty. Checking reasons...")
            
            # Checking pivot
            try:
                pivoted = (agg.pivot(
                    values=["sum_oil_rate", "well_count"], 
                    index=group_by_cols,
                    columns="date"
                ))
                print("\nPivot result:")
                print(pivoted)
                
                # Checking if columns for calculation exist
                rate_t0_col = f"sum_oil_rate_{t0}"
                rate_t1_col = f"sum_oil_rate_{t1}"
                print(f"\nChecking if columns {rate_t0_col} and {rate_t1_col} exist:")
                if rate_t0_col in pivoted.columns and rate_t1_col in pivoted.columns:
                    print("Both columns are present")
                else:
                    print("Required columns are missing:")
                    print("Columns in pivot:", pivoted.columns)
            except Exception as e:
                print(f"Error creating pivot: {e}")
    else:
        print("Not enough unique dates for decline rate calculation (minimum 2 required)")
    
except Exception as e:
    print(f"Error analyzing data: {e}")
