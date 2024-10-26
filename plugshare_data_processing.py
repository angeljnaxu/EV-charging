import pandas as pd
import re
import os
import chardet
import ast
import numpy as np

# definitions of the functions
def geoloc_data_cleaning(filepath, filename):
    df = pd.read_csv(filepath + "/" + filename)

    for index, row in df.iterrows():
        if row["Station Name"] == "share":
            df = df.drop(index)
            print("Station dropped due to case of 'share' in row" + row + ". Please check raw data.")
    
    #create a boolean mask for dropping NA/null rows
    df = df[df['Station Name'].notna()]
                  
    # #reads the recalculated list
    # recalc_file = "/Users/salataresearchassistant/Desktop/Seamless EV Charging/EV_Charging/Spring24_IDs_Recalc.txt"
    # with open(recalc_file, 'r') as file:
    #     lines = file.readlines()
    # recalc_list = [line.strip() for line in lines]

    # #takes only the chargers that are in the recalc list
    # #COMMENT THIS SECTION TO TOGGLE IF PUTTING INTO THE RECALC FILE OR NOT
    # mask = df['Station ID'].isin(recalc_list)
    # df = df[mask]

    #remove restricted stations
    df = df.drop(df[df['Restricted'] == True].index)

    lats = []
    lons = []
    pricing = []

    list_based_columns = ['Plug Status', 'Real Time Data Availability', 'Type', 'Wattage', 'Number of Plugs']

    for index, info in enumerate(df['Station Info']):
        try:
            if not info:
                #if 'Station Info' is empty, append default values
                lats.append(np.nan)
                lons.append(np.nan)
                pricing.append(np.nan)
                continue  #move to the next iteration
            
            #remove surrounding brackets if present
            info = info.strip('[]')
            
            #extract latitude and longitude
            lat_lon_pattern = re.compile(r'(-?\d{1,3}\.\d+)')
            lat_lon_matches = lat_lon_pattern.findall(info)
            
            if len(lat_lon_matches) >= 2:
                lat = float(lat_lon_matches[0])
                lon = float(lat_lon_matches[1])
            else:
                lat = np.nan
                lon = np.nan
            
            lats.append(lat)
            lons.append(lon)
            
            #extract pricing information
            payment_required_idx = info.find('Payment Required')
            if payment_required_idx != -1:
                #extract substring starting from 'Payment Required'
                payment_info = info[payment_required_idx:]
                
                #define end markers for the pricing info
                end_markers = ['View station level pricing details', '"']
                end_indices = [payment_info.find(marker) for marker in end_markers if payment_info.find(marker) != -1]
                
                if end_indices:
                    end_idx = min(end_indices)
                    pricing_info = payment_info[len('Payment Required'):end_idx].strip().strip(':').strip()
                    pricing.append(pricing_info if pricing_info else np.nan)
                else:
                    pricing.append(np.nan)
            else:
                pricing.append(np.nan)
        
        except Exception as e:
            print(f"Error processing 'Station Info' at row {index}: {e}")
            lats.append(np.nan)
            lons.append(np.nan)
            pricing.append(np.nan)

    df["Latitude"] = lats
    df["Longitude"] = lons
    df["Pricing"] = pricing

    def determine_real_time(row):
        try:
            if pd.isnull(row['L3 Plugs with Real Time Data']) or pd.isnull(row['Total L3 Plugs']):
                return 'Unknown'
            if row['L3 Plugs with Real Time Data'] == row['Total L3 Plugs']:
                return 'All Plugs'
            elif row['L3 Plugs with Real Time Data'] > 0:
                return 'Some Plugs'
            else:
                return 'None'
        except:
            return 'Unknown'
    
    df['Real Time?'] = df.apply(determine_real_time, axis=1)

    available_plugs = []
    in_use_plugs = []
    unavailable_plugs = []

    for index, row in df.iterrows():
        status = row['Plug Status']
    
        available = 0
        in_use = 0
        unavailable = 0

        status = status.lstrip('[').rstrip(']').replace("'", '')
        status_lst = status.split(', ')

        plug_types = row['Type'].lstrip('[').rstrip(']').replace("'", '').split(', ')
        for i in range(len(plug_types)):
            if plug_types[i] == 'J-1772':
                status_lst = status_lst[:i] + status_lst[i+3:]

        for s in status_lst:
            if s[2:] == 'Available' or s[3:] == 'Available':
                available += int(s[0:2].strip())
            elif s[2:] == 'In Use' or s[3:] == 'In Use':
                in_use += int(s[0:2].strip())
            elif s[2:] == 'Unavailable' or s[3:] == 'Unavailable':
                unavailable += int(s[0:2].strip())
            else:
                print('something went wrong')
                print(s)

        available_plugs.append(available)
        in_use_plugs.append(in_use)
        unavailable_plugs.append(unavailable)

    df['Total Available Chargers'] = available_plugs
    df['Total In Use Chargers'] = in_use_plugs
    df['Total Unavailable Chargers'] = unavailable_plugs

    location_types = []
    for location_type in df['Station Type']:
        try:
            location_type = location_type.lstrip("['").rstrip("']")
            location_types.append(location_type)
        except:
            location_types.append("NA")

    df['Location Type'] = location_types

#splitting rows by charging provider
    expanded_rows = []

    for _, row in df.iterrows():
        #parse 'Networked' column into a list
        providers = ast.literal_eval(row['Networked']) if isinstance(row['Networked'], str) else []
            
        if not providers:
            #if no more providers listed, append the original row as is
            expanded_rows.append(row.to_dict())
            continue  #move to the next iteration
            
        #process each provider
        unique_providers = set(providers)
        for provider in unique_providers:
            provider_indices = [i for i, p in enumerate(providers) if p == provider]
                
            new_row = row.copy()
            new_row['Charging Provider'] = provider
                
            #process list-based columns **** this needs work???
            for col in list_based_columns:
                try:
                    #parse the column into a list
                    col_data = ast.literal_eval(row[col]) if isinstance(row[col], str) else []
                        
                     #extract data corresponding to the current provider
                    provider_col_data = [col_data[i] for i in provider_indices] if col_data else []
                        
                    new_row[col] = provider_col_data if provider_col_data else np.nan
                except:
                    new_row[col] = np.nan  #assign null value if parsing fails
                
            # Uncomment if you aren't parsing through the "Plug More Details" column!
            # expanded_rows.append(new_row.to_dict())

            # NEW: Parse 'Plug More Details' column and duplicate rows accordingly
            more_details = ast.literal_eval(row['Plug More Details']) if isinstance(row['Plug More Details'], str) else []

            if more_details:
                for detail in more_details:
                    # Create a new row for each detail
                    detail_row = new_row.copy()
                    detail_row['Plug More Details'] = detail  # Replace with the specific detail

                    # Append the new row to expanded_rows
                    expanded_rows.append(detail_row.to_dict())

    #create a new DataFrame from the expanded rows
    processed_df = pd.DataFrame(expanded_rows)

    #final check to ensure the lengths match
    if len(processed_df) != len(expanded_rows):
        raise ValueError(f"Length of processed data ({len(processed_df)}) does not match expected length ({len(expanded_rows)})")

    
    final_data = processed_df[["Data Collection Datetime", "Interstate", "Station ID", "Station Name", "Location Type", "Latitude", "Longitude", 
                     "Pricing", "Total L3 Plugs", "L3 Plugs with Real Time Data", "Real Time?", 
                     "Total Available Chargers", "Total In Use Chargers", "Total Unavailable Chargers", "Charging Provider","Plug More Details"]]

    finalfilename = 'ChatGPT_fulltestfile_plugsplit.csv'
    final_data.to_csv(filepath + "/EV_Charging/processed_runs/" + finalfilename)
    return 'Done'

def run_processing(filepath):
    # Function for processing the entirety of a folder with raw data runs
    for filename in os.listdir(filepath):
        if filename == '.DS_Store':
            continue  # Skip .DS_Store files
        file_path = os.path.join(filepath, filename)
        try:
            # Detect the encoding of the file
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            print(f"Detected encoding {encoding} for file {file_path}")
            
            # Ensure the file is opened with the detected encoding
            with open(file_path, 'r', encoding=encoding) as f:
                # Add the logic to process the file using the data cleaning function
                data = f.read()
                print(geoloc_data_cleaning(filepath, filename))
                
        except UnicodeDecodeError as e:
            print(f"Encoding error in file {file_path}: {e}")
        except Exception as e:
            print(f"An error occurred while processing the file {file_path}: {e}")
            pass

#USE THIS FOR ITERATING THROUGH THE ENTIRETY OF THE FOLDER
# run_processing('/Users/salataresearchassistant/Desktop/Seamless EV Charging/EV_Charging/raw_data_runs/08-13-2024')

from datetime import date
def run_interstate():
    #data processing by interstate
    interstates = [95, 90, 80, 75, 10, 5]
    dates = [str(date.today())]
    for date in dates:
        for i in interstates:
            df = pd.read_csv('/Users/salataresearchassistant/Desktop/Seamless EV Charging/raw_data_runs/I-' + str(i) + '_plugshare_scrape_' + date + '.csv')
            print(geoloc_data_cleaning('I-' + str(i) + '_plugshare_scrape_' + date + '.csv'))
            # except Exception as e:
            #     print(e)
            #     pass
    
def run_timezone(filepath, timezones, times_of_day, dates):
    #data processing by timezones/time of day/date
    for d in dates:
        for tz in timezones:
            for t in times_of_day:
                try:  
                    print(geoloc_data_cleaning(filepath, tz + '_plugshare_scrape_' + str(d) + '_' + t + '.csv'))
                except Exception as e:
                    print(tz + '_plugshare_scrape_' + str(d) + '_' + t + '.csv')
                    print(e)
                    pass

# Insert file path into this call
fp = '/Users/angelinaxu/Desktop'
timezones = ['pacific', 'central', 'eastern', 'mountain']
times_of_day = ['OffPeak', 'EveningRush', 'MorningRush']
dates = ['2024-03-28']
#run_timezone(fp, timezones, times_of_day, dates)

# personal section for running the functions
filename = 'EV_Charging/raw_data_runs/10-3_MAXDATA_sample_unrestricted_plugshare_scrape_2024-10-22_OffPeak.csv'
geoloc_data_cleaning(fp, filename)