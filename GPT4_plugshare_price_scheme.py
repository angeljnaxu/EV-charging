import requests
import os
import pandas as pd
import numpy as np
import csv
import json

# Set up the OpenAI API key and endpoint URL
endpoint_url = 'https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1/chat/completions'
api_key = 'h416pyK4fW3AfQ76HrFsKoCIapFslNTswf1R516uy7jurXDU'# Replace with your actual API key
headers = {
    'Content-Type': 'application/json',
    'api-key': api_key
}

# full scientifically rigorous test file
pre_tier_csv_name = "processed_runs/ChatGPT_SHORTDATAtestfile_plugsplit.csv"
# test file for new functionalities!
# pre_tier_csv_name = "processed_runs/ChatGPT Test Files/ChatGPT_condensedtestfile_plugsplit.csv"

post_tier_json_name = "processed_runs/ChatGPT Test Files/10-24_ChatGPT_SHORTDATAtestfile_plugsplit_gpt4o.jsonl"
post_tier_csv_name = "processed_runs/ChatGPT Test Files/10-24_ChatGPT_SHORTDATAtestfile_plugsplit_gpt4o.csv"

# create the dataframe
df = pd.read_csv(pre_tier_csv_name)
df['prompt'] = df['Pricing'] + ' | Additional Details: ' + df['Plug More Details']

# Get the current working directory
cwd = os.getcwd()
# Set the paths for the input and output files
csv_file_path = os.path.join(cwd, pre_tier_csv_name)
jsonl_file_path = os.path.join(cwd, post_tier_json_name)

# Read CSV file and create a list of dictionaries
with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    data = [row for row in reader]

# Write JSONL file
with open(jsonl_file_path, 'w', encoding='utf-8') as jsonlfile:
    for row in data:
        json.dump(row, jsonlfile)
        jsonlfile.write('\n')

# Load the dataset again
df1 = pd.read_json(post_tier_json_name, lines=True)
df1['prompt'] = df1['Pricing'] + ' | Additional Details: ' + df1['Plug More Details']

# Ensure 'level_2_price' and 'fast_charge_price' columns exist in the DataFrame
if 'level_2_price' not in df1.columns:
    df1['level_2_price'] = None

if 'fast_charge_price' not in df1.columns:
    df1['fast_charge_price'] = None

batch_size = 10
total_records = len(df1)

for start in range(0, total_records, batch_size):
    # Define the end index for the batch
    end = min(start + batch_size, total_records)
    
    # Create a batch of payloads for the requests
    batch_payload = []
    
    for i in range(start, end):
        # Assuming 'prompt' is a column in your DataFrame with the necessary data
        prompt_value = df1.loc[i, 'prompt']
        payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": (
                "I will give you an input. Write a total of two words, separated by a space."
                "The first word should describe the type of charger in the input, which is"
                "'slow' if the kWh value listed in 'Plug More Details' is strictly below 50 kWH"
                "or 'fast' in all other cases. Using the data written"
                "in the 'Pricing' and 'Plug More Details' columns, write the second word to describe"
                "the pricing scheme. The word can either be 'free', 'energy', 'tiered-kWH', 'tiered-time',"
                "'time-of-use', 'time', or 'unknown'. The word should be based on the price and whether"
                "it is energy-based (includes 'energy', 'tiered', 'time-of-use' or time-based."
                "If there are multiple charging rates, it is tiered if the price is based on" 
                "previous usage and time-of-use if it's based on the time of day. Do not"
                "include parking, idle, or any other fees when calculating the charging"
                "rate. If there is a flat rate/fee per transaction in addition to"
                "one of the other types of pricing schemes, disregard the flat rate/fee."
                "Also ignore statements about stations having variable pricing. If there is"
                "no charging rate, the word should be 'free', but if the charging/pricing"
                "rate for all chargers is unknown, the word should be 'unknown'. For example,"
                "'$0.25kWh' -> energy, '$1/hour' -> time, '$0.50/kWh for the first 10 kWh, then $0.25/kWh' -> tiered-kWH,"
                "'$0.50/kWh for the first 3 hours, then $0.25/kWh' -> tiered-time, '$0.46 per kWh, 12:00AM"
                "- 3:00AM and $0.63 per kWh, 3:00AM - 1:00PM' -> time-of-use, 'No"
                "charge' -> free."
            )},
            {"role": "user", "content": f"Analyze pricing structure: {prompt_value}"}
        ],
        "temperature": 0.7
        }
        batch_payload.append(payload)

    # Send batch request
    try:
        # Assuming you're sending one request per batch, adjust as necessary for your API's batch capabilities
        for j, payload in enumerate(batch_payload):
            response = requests.post(endpoint_url, headers=headers, json=payload)
            response_json = response.json()

             # Extract the output from the API response
            output = response_json['choices'][0]['message']['content']
            word1, word2 = output.split(" ")
            
            # Ensure the columns are correctly set as object type
            df1['level_2_price'] = df1['level_2_price'].astype(object)
            df1['fast_charge_price'] = df1['fast_charge_price'].astype(object)
            
            # Update the correct row in the DataFrame
            if word1 == "slow":
                df1.at[start + j, 'level_2_price'] = word2
                df1.at[start + j, 'fast_charge_price'] = 0
            else:
                df1.at[start + j, 'fast_charge_price'] = word2
                df1.at[start + j, 'level_2_price'] = 0

    except Exception as e:
        print(f"Error processing batch starting at record {start}: {e}")
        # In case of error, mark the entire batch with error flags
        for k in range(start, end):
            df1.at[k, 'level_2_price'] = -1
            df1.at[k, 'fast_charge_price'] = -1

# Save the updated DataFrame to JSONL format
df1.to_json(jsonl_file_path, orient='records', lines=True)
print(f"Data successfully saved to a json: {jsonl_file_path}")

# Converting the JSONL file to a CSV file that is also saved
data = []
with open(jsonl_file_path, 'r') as file:
    for line in file:
        data.append(json.loads(line))

df = pd.DataFrame(data)
df.to_csv(post_tier_csv_name, index=False)
print(f"Data successfully saved to a csv: {post_tier_csv_name}")