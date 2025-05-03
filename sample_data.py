import polars as pl
import numpy as np
from datetime import datetime, timedelta
import os

def generate_sample_data(num_wells=500):
    """
    Generates sample data for testing the application
    
    Args:
        num_wells: Number of wells to generate
    
    Returns:
        tuple: (prod_df, events_df) - DataFrame with production data and events
    """
    # Generate basic data
    np.random.seed(42)
    
    # List of wells
    well_ids = [f"WELL_{i:03d}" for i in range(1, num_wells + 1)]
    
    # Horizons/layers - add more horizons
    horizons = ["A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "D1", "D2"]
    
    # Fields
    fields = ["North", "South", "West", "East", "Central"]
    
    # Event types
    event_types = ["Workover", "Well intervention", "Change of horizon", "Optimization", "Pump replacement", 
                  "Hydraulic fracturing", "Treatment of the near-well zone", "Isolation of water influx"]
    
    # Dates for two years
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 4, 30)
    
    # Generate production data
    records = []
    current_date = start_date
    
    # For optimization, we will generate data monthly, not daily
    while current_date <= end_date:
        for well in well_ids:
            # Determine the horizon for the well (constant for each well)
            horizon_idx = int(well.split("_")[1]) % len(horizons)
            horizon = horizons[horizon_idx]
            
            # Determine the field for the well
            field_idx = int(well.split("_")[1]) % len(fields)
            field = fields[field_idx]
            
            # Base rate depends on the horizon and well
            base_rate = 50 + (horizon_idx * 20) + (int(well.split("_")[1]) % 30)
            
            # Add natural decline (exponential)
            months_from_start = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)
            decline_factor = np.exp(-0.015 * months_from_start)
            
            # Add seasonality (slightly lower in winter)
            month = current_date.month
            seasonal_factor = 1.0 - 0.1 * (month == 12 or month <= 2)
            
            # Add random noise
            noise = np.random.normal(1.0, 0.05)
            
            # Final oil rate
            oil_rate = base_rate * decline_factor * seasonal_factor * noise
            
            # Water cut increases over time
            water_cut_base = 0.2 + (0.01 * months_from_start)
            water_cut = min(0.95, water_cut_base + np.random.normal(0, 0.05))
            
            # Liquid rate
            liquid_rate = oil_rate / (1 - water_cut) if water_cut < 1.0 else 0.0
            
            # Gas factor
            gas_factor = 100 + (horizon_idx * 50) + np.random.normal(0, 10)
            
            # Gas rate
            gas_rate = oil_rate * gas_factor
            
            # Working days in the month (some wells may be idle)
            working_days = np.random.randint(20, 31) if np.random.random() > 0.05 else np.random.randint(0, 20)
            
            records.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "uwi": well,
                "horizon": horizon,
                "field": field,
                "oil_rate": round(oil_rate, 2),
                "liquid_rate": round(liquid_rate, 2),
                "water_cut": round(water_cut, 4),
                "gas_rate": round(gas_rate, 2),
                "working_days": working_days
            })
        
        # Move to the next month
        year = current_date.year + ((current_date.month + 1) // 13)
        month = (current_date.month % 12) + 1
        current_date = datetime(year, month, 1)
    
    # Create DataFrame with production data
    prod_df = pl.DataFrame(records)
    
    # Generate events
    event_records = []
    
    # For each well, generate several events
    for well in well_ids:
        # Number of events for the well (from 0 to 5)
        num_events = np.random.randint(0, 6)
        
        for _ in range(num_events):
            # Random event date
            event_date = start_date + timedelta(days=np.random.randint(30, (end_date - start_date).days - 30))
            
            # Random event type
            event_type = np.random.choice(event_types)
            
            # Determine the horizon for the well
            horizon_idx = int(well.split("_")[1]) % len(horizons)
            horizon = horizons[horizon_idx]
            
            # Determine the field for the well
            field_idx = int(well.split("_")[1]) % len(fields)
            field = fields[field_idx]
            
            # Add the effect of the event (for some types)
            effect = round(np.random.uniform(1.0, 3.0), 2) if event_type in ["Workover", "Hydraulic fracturing", "Treatment of the near-well zone"] else 0.0
            
            event_records.append({
                "uwi": well,
                "event_date": event_date.strftime("%Y-%m-%d"),
                "event_type": event_type,
                "horizon": horizon,
                "field": field,
                "effect": effect,
                "description": f"{event_type} for well {well} on horizon {horizon}"
            })
    
    # Create DataFrame with events
    events_df = pl.DataFrame(event_records)
    
    return prod_df, events_df

def save_sample_data(num_wells=500, format="csv"):
    """
    Saves the generated data in the specified format
    
    Args:
        num_wells: Number of wells to generate
        format: Format to save the data ("csv" or "parquet")
    """
    prod_df, events_df = generate_sample_data(num_wells)
    
    # Create the directory for test data if it does not exist
    os.makedirs("test_data", exist_ok=True)
    
    # Save the data in the specified format
    if format.lower() == "csv":
        prod_df.write_csv("test_data/prod_data.csv")
        events_df.write_csv("test_data/events_data.csv")
        print(f"Data saved in CSV format in 'test_data' directory")
        print(f"- Production data: {len(prod_df)} records for {num_wells} wells")
        print(f"- Events data: {len(events_df)} records")
    else:
        prod_df.write_parquet("test_data/prod_data.parquet")
        events_df.write_parquet("test_data/events_data.parquet")
        print(f"Data saved in Parquet format in 'test_data' directory")
        print(f"- Production data: {len(prod_df)} records for {num_wells} wells")
        print(f"- Events data: {len(events_df)} records")
    
    return prod_df, events_df

if __name__ == "__main__":
    save_sample_data(num_wells=500, format="csv")
