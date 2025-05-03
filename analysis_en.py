import polars as pl
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from utils import calculate_decline_rate, safe_to_pandas
from logger import logger, safe_log

# Create English paths
current_dir = os.getcwd()
test_data_dir = os.path.join(current_dir, "test_data")
prod_file = os.path.join(test_data_dir, "prod_data.csv")
events_file = os.path.join(test_data_dir, "events_data.csv")

try:
    # Load data
    print(f"Loading production data from: {prod_file}")
    prod_df = pl.read_csv(prod_file)
    print(f"Number of rows in production data: {len(prod_df)}")
    print(f"Columns in production data: {prod_df.columns}")
    print("Sample production data:")
    print(prod_df.head(5))
    
    print(f"\nLoading events data from: {events_file}")
    events_df = pl.read_csv(events_file)
    print(f"Number of rows in events data: {len(events_df)}")
    print(f"Columns in events data: {events_df.columns}")
    print("Sample events data:")
    print(events_df.head(5))
    
    # Analyze production data
    print("\nProduction data analysis:")
    print(f"Unique wells: {prod_df['well_id'].unique().to_list()}")
    print(f"Number of wells: {len(prod_df['well_id'].unique())}")
    print(f"Unique horizons: {prod_df['horizon'].unique().to_list()}")
    unique_dates = prod_df["date"].unique().sort()
    print(f"Number of unique dates: {len(unique_dates)}")
    print(f"Minimum date: {min(unique_dates)}")
    print(f"Maximum date: {max(unique_dates)}")
    
    # Check data for decline rate calculation
    start_date = "2023/01/01"
    end_date = "2024/01/01"
    print(f"\nCalculating decline rate for period: {start_date} - {end_date}")
    
    # Check date filtering
    filtered_df = prod_df.filter(
        (pl.col("date") >= start_date) & 
        (pl.col("date") <= end_date)
    )
    print(f"Number of rows after date filtering: {len(filtered_df)}")
    
    # Check if we have data in the filtered range
    if len(filtered_df) == 0:
        print("No data in the specified date range!")
        exit()
    
    # Check grouping by horizon
    group_by_cols = ["horizon"]
    grouped = filtered_df.group_by(["date"] + group_by_cols)
    agg = grouped.agg([
        pl.sum("oil_rate").alias("sum_oil_rate"),
        pl.count("well_id").alias("well_count")
    ])
    print("\nGrouping result by horizon:")
    print(agg.head(5))
    
    # Check if we have data for two dates (t0 and t1)
    unique_dates = agg["date"].unique().sort()
    print(f"\nUnique dates after grouping: {unique_dates.to_list()}")
    
    if len(unique_dates) >= 2:
        t0 = min(unique_dates)
        t1 = max(unique_dates)
        print(f"Start date (t0): {t0}")
        print(f"End date (t1): {t1}")
        
        # Perform decline rate calculation
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
            
            # Check pivot
            try:
                pivoted = (agg.pivot(
                    values=["sum_oil_rate", "well_count"], 
                    index=group_by_cols,
                    columns="date"
                ))
                print("\nPivot result:")
                print(pivoted)
                
                # Check if columns for calculation exist
                rate_t0_col = f"sum_oil_rate_{t0}"
                rate_t1_col = f"sum_oil_rate_{t1}"
                print(f"\nChecking if columns {rate_t0_col} and {rate_t1_col} exist:")
                if rate_t0_col in pivoted.columns and rate_t1_col in pivoted.columns:
                    print("Both columns are present")
                    
                    # Check if we have non-zero values
                    non_zero_t0 = pivoted.filter(pl.col(rate_t0_col) > 0)
                    non_zero_t1 = pivoted.filter(pl.col(rate_t1_col) > 0)
                    print(f"Records with non-zero {rate_t0_col}: {len(non_zero_t0)}")
                    print(f"Records with non-zero {rate_t1_col}: {len(non_zero_t1)}")
                    
                    # Check if we have wells with data at both t0 and t1
                    if len(non_zero_t0) > 0 and len(non_zero_t1) > 0:
                        common_wells = set(non_zero_t0[group_by_cols[0]].to_list()) & set(non_zero_t1[group_by_cols[0]].to_list())
                        print(f"Wells with data at both t0 and t1: {common_wells}")
                        print(f"Number of wells with data at both dates: {len(common_wells)}")
                    else:
                        print("No wells with non-zero production at both dates")
                else:
                    print("Required columns are missing:")
                    print(f"Columns in pivot: {pivoted.columns}")
            except Exception as e:
                print(f"Error creating pivot: {e}")
    else:
        print("Not enough unique dates for decline rate calculation (minimum 2 required)")
    
except Exception as e:
    print(f"Error analyzing data: {e}")
