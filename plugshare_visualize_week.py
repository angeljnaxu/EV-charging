import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

import pandas as pd
import os
import glob

plt.style.use('seaborn-v0_8-notebook')

# Define the path to the extracted data directory
extracted_dir_path = '/Users/salataresearchassistant/Desktop/Seamless EV Charging'

# Function to extract date from filename and add it as a new column
def add_date_from_filename(file_path):
    filename = os.path.basename(file_path)
    date_str = filename.split('_')[3]  # Assumes date is the fourth component in the filename
    return date_str

# Load the raw data files and combine them into a single DataFrame
raw_data_runs_path = os.path.join(extracted_dir_path, 'EV_Charging', 'raw_data_runs')
raw_data_files = glob.glob(os.path.join(raw_data_runs_path, '*_OffPeak.csv'))

df_list = []
for file in raw_data_files:
    date_str = add_date_from_filename(file)
    df = pd.read_csv(file)
    df['date'] = date_str
    df_list.append(df)

raw_data = pd.concat(df_list, ignore_index=True)

# Convert date column to datetime and filter data on or after March 25th, 2024
raw_data['date'] = pd.to_datetime(raw_data['date'])
raw_data = raw_data[raw_data['date'] >= '2024-03-25']

# Extract day of the week and week number
raw_data['day_of_week'] = raw_data['date'].dt.day_name()
raw_data['week'] = raw_data['date'].dt.isocalendar().week

# Define highways of interest
highways = ['I-95', 'I-5', 'I-10', 'I-75', 'I-80', 'I-90']

# Function to plot data for a specific highway
def plot_data_for_highway(highway):
    # Filter data for the specific highway
    highway_data = raw_data[raw_data['highway'] == highway]
    
    # Sort the days of the week
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Plot the data week by week
    plt.figure(figsize=(10, 6))
    
    for week in highway_data['week'].unique():
        weekly_data = highway_data[highway_data['week'] == week]
        summary = weekly_data.groupby('day_of_week')['available_chargers'].mean() * 100
        summary = summary.reindex(days_of_week)
        plt.plot(summary.index, summary, marker='o', linestyle='dashed', linewidth=2, label=f'Week {week}')
    
    plt.xlabel('Day of Week')
    plt.ylabel('Percentage of Available Chargers')
    plt.title(f'Percentage of Available Chargers by Day of Week for {highway}')
    plt.ylim(0, 100)
    plt.legend(title='Week Number', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0f}%'))
    plt.tight_layout()
    plt.show()

# Plot for each highway
for highway in highways:
    plot_data_for_highway(highway)