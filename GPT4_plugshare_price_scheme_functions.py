import requests
import os
import pandas as pd
import numpy as np
import csv
import json
import chardet
from functools import reduce

# Set up the OpenAI API key and endpoint URL
endpoint_url = 'https://go.apis.huit.harvard.edu/ais-openai-direct-limited-schools/v1/chat/completions'
api_key = 'h416pyK4fW3AfQ76HrFsKoCIapFslNTswf1R516uy7jurXDU'# Replace with your actual API key
headers = {
    'Content-Type': 'application/json',
    'api-key': api_key
}

# DEFINE BASIC ACTIONS 
def run_GPT(pre_tier_csv_name):
    # create the dataframe
    df = pd.read_csv(pre_tier_csv_name)
    df['prompt'] = 'Pricing Details: ' + df['Pricing'] + ' | Additional Details: ' + df['Plug More Details'] + '| Charging Provider: ' + df['Charging Provider'] + '| Charging Scheme: ' + df['Charging Scheme']
    # df['prompt'] = 'Pricing Details: ' + df['Pricing'] + ' | Additional Details: ' + df['Plug More Details'] + '| Charging Provider: ' + df['Charging Provider'] + '| Charging Scheme: ' + df['fast_charge_scheme']

    # Get the current working directory
    cwd = os.getcwd()
    # Set the paths for the input and output files
    csv_file_path = os.path.join(cwd, pre_tier_csv_name)

    # Read CSV file and create a list of dictionaries
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]

    # Store JSON data in memory instead of saving to file
    json_data_in_memory = [json.dumps(row) for row in data]

    # Load JSON data from memory instead of file
    df1 = pd.DataFrame([json.loads(line) for line in json_data_in_memory])
    df1['prompt'] = 'Pricing Details: ' + df1['Pricing'] + ' | Additional Details: ' + df1['Plug More Details'] + '| Charging Provider: ' + df1['Charging Provider'] + '| Charging Scheme: ' + df1['Charging Scheme']

    return df1

# DEFINE THE FUNCTIONS FOR EACH TYPE OF PROMPT (preliminary & by scheme)
def preliminary_scheme(pre_tier_csv_name, post_tier_csv_name):
        # create the dataframe
    df = pd.read_csv(pre_tier_csv_name)
    df['prompt'] = 'Pricing Details: ' + df['Pricing'] + ' | Additional Details: ' + df['Plug More Details'] + '| Charging Provider: ' + df['Charging Provider']

    # Get the current working directory
    cwd = os.getcwd()
    # Set the paths for the input and output files
    csv_file_path = os.path.join(cwd, pre_tier_csv_name)

    # Read CSV file and create a list of dictionaries
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]

    # Store JSON data in memory instead of saving to file
    json_data_in_memory = [json.dumps(row) for row in data]

    # Load JSON data from memory instead of file
    df1 = pd.DataFrame([json.loads(line) for line in json_data_in_memory])
    df1['prompt'] = 'Pricing Details: ' + df1['Pricing'] + ' | Additional Details: ' + df1['Plug More Details'] + '| Charging Provider: ' + df1['Charging Provider']

    # Ensure the columns are correctly set as object type
    new_column = 'Charging Scheme'
    df1[new_column] = None
    df1[new_column] = df1[new_column].astype(object)

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
                    'I will give you an input. Write a total of one phrase.'  
                    'Using the data written in the "Pricing" , "Plug More Details" , and "Charging Provider" columns,'  
                    'The 1st phrase is a comma-separated list of schemes that apply to the price of'  
                    'using a charger. The possible pricing schemes are "free", "energy", "tiered-kWh", "tiered-time",'  
                    '"time-of-use", "time", "other", or "unknown". Do not include parking, idle, or any other fees when calculating'  
                    'the charging rate. Also, ignore statements about stations having variable pricing. If the cost'  
                    'to charge is free, the list should include "free". If there is a single'  
                    'rate that only depends on how many kWh you have charged, "energy" should be included'  
                    'in the list. If there are multiple charging rates, and it is tiered by'  
                    'how many kWh you have previously charged, "tiered-kWh" should be on the list.'  
                    'If there are multiple charging rates that instead depend on how long you have'  
                    'previously been charging for, "tiered-time" should be on the list. If the price is'  
                    'not based on previous usage but instead based on the time of day, "time-of-use"'  
                    'should be on the list. If there is a single rate that only depends'  
                    'on how long you charge for, "time" should be on the list. If any'  
                    'combination of the previously mentioned schemes does not fully cover the pricing scheme, the word "other"'  
                    'should be on the list. If the charging/pricing rate for the charger is not'  
                    'available, the word "unknown" should be included on the list. If "unknown" is in the list,'  
                    'no other schemes should be on the list. For the 1st phrase, if there'  
                    'is a mismatch of information between the Pricing information between "Pricing: " and "| Charging Provider: "'  
                    'and the Additional Details information between "| Charging Provider: " and "| Additional Details: "'  
                    'in regards to the charging pricing scheme, prefer the Additional Details information, and extract those'  
                    'details from only the Additional Details information. However, if there is information in Pricing but'  
                    'not in Additional Details about the pricing scheme, extract from all the available information.'  
                    'The exception is for the provider EVCS, where if the charging scheme says "free"'  
                    'before giving a price, extract only the price, and ignore the previous "free" statement.'  
                    'Note: If a time range spans a full 24 hours (e.g., 5 PM to 5 PM),'  
                    'classify it as "energy" instead of "time-of-use."'  
                    'For example,'  
                    '"No charge" -> free,'  
                    '"$0.25kWh" -> energy,'  
                    '"$0.30kWh 5PM - 5PM" -> energy,'  
                    '"$0.50/kWh for the first 10 kWh, then $0.25/kWh" -> tiered-kWh,'  
                    '"$0.50/hour for the first 3 hours, then $0.25/hour" -> tiered-time,'  
                    # '"$0.50/min up to 20 kWh, $0.25/min to 40 kWh, then $0.20/min" -> tiered-time-kWh,'  
                    '"$0.46 per kWh, 12:00AM - 3:00AM and $0.63 per kWh, 3:00AM - 1:00PM" -> time-of-use,'  
                    '"$1/hour" -> time.'  
                    '"Pricing: $3/hr … |Additional Details: $0.25/kWh” -> energy'  
                    '"Pricing: $3/hr … |Additional Details: unknown” -> time'  
                    '"...| Charging Provider: EVCS | Additional Details: free 0.25/kWh -> energy "'
                    'Additionally, we are only interested in the price of the fast chargers and will disregard any information'
                    'specifically labeled for only level 2 chargers. If you see different information about "DCFC"/"DC" vs. "level 2",'
                    'use the information given in "DCFC"/"DC" and drop what "level 2" says.'  
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
                phrase = response_json['choices'][0]['message']['content']
                df1.at[start + j, new_column] = str(phrase)

        except Exception as e:
            print(f"Error processing batch starting at record {start}: {e}")
            # In case of error, mark the entire batch with error flags
            for k in range(start, end):
                df1.at[k, new_column] = -1

    # Store the updated DataFrame as JSON lines in memory
    jsonl_data_in_memory = df1.to_json(orient='records', lines=True).splitlines()
    print("Data successfully stored in memory as JSON lines.")

    # Converting the in-memory JSON lines to a list of dictionaries
    data = [json.loads(line) for line in jsonl_data_in_memory]

    df = pd.DataFrame(data)
    df.to_csv(post_tier_csv_name, index=False)
    print(f"Data successfully saved to a csv: {post_tier_csv_name}")

def energy_extraction(df1):
    # CLEAN DF1 OF ALL ROWS THAT ARE NOT THE RIGHT PRICE SCHEME
    df1 = df1[df1['Charging Scheme'].str.contains('energy', na=False)].reset_index(drop=True)

    # RUN THE GPT API WITH YOUR CHOSEN FILE TYPE
    column = 'Energy Price'
    df1[column] = None
    df1[column] = df1[column].astype(object)
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
                    'I will give you an input. Write a total of 1 phrase.'
                    'Using the data written in the "Pricing" , "Plug More Details" , "Charging Provider", and "Charging Scheme" columns,'
                    'This new phrase should be the specific price per kWh to charge formatted as "$[price] per kWh". For example,'  
                    'Statement = "$0.25kWh" -> $0.25 per kWh'
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

                # Extract the output from the API response & store
                phrase = response_json['choices'][0]['message']['content']
                df1.at[start + j, column] = str(phrase)

        except Exception as e:
            print(f"Error processing batch starting at record {start}: {e}")
            # In case of error, mark the entire batch with error flags
            for k in range(start, end):
                df1.at[k, column] = -1

    return df1

def TOU_extraction(df1):
    # CLEAN DF1 OF ALL ROWS THAT ARE NOT THE RIGHT PRICE SCHEME
    df1 = df1[df1['Charging Scheme'].str.contains('time-of-use', na=False)].reset_index(drop=True)

    # RUN THE GPT API WITH YOUR CHOSEN FILE TYPE
    column_list = ['12:00-1:00 AM Price', '1:00-2:00 AM Price', '2:00-3:00 AM Price', '3:00-4:00 AM Price', '4:00-5:00 AM Price', 
                   '5:00-6:00 AM Price', '6:00-7:00 AM Price', '7:00-8:00 AM Price', '8:00-9:00 AM Price', '9:00-10:00 AM Price',
                   '10:00-11:00 AM Price', '11:00AM - 12:00PM Price', '12:00-1:00 PM Price', '1:00-2:00 PM Price', '2:00-3:00 PM Price',
                   '3:00-4:00 PM Price', '4:00-5:00 PM Price', '4:00-5:00 PM Price', '5:00-6:00 PM Price', '6:00-7:00 PM Price',
                   '7:00-8:00 PM Price', '8:00-9:00 PM Price', '9:00-10:00 PM Price', '10:00-11:00 PM Price', '11:00PM - 12:00AM Price']
    for column in column_list:
        df1[column] = None
        df1[column] = df1[column].astype(object)
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
                    'I will give you an input. Write a total of 24 phrases, with each individual phrase separated by |.'
                    'Using the data written in the "Pricing" , "Plug More Details" , "Charging Provider", and "Charging Scheme" columns,'
                    'Consider the next 24 phrases as an individual set of phrases.'
                    '1st phrase: This phrase describes the price for charging from 12:00 AM -1:00 AM, if applicable.'  
                    'The phrase should be formatted as "$[price] per kWh".'
                    'Phrases 2 through 24 should be the same as phrase 1 except for each successive hour.'  
                    'Phrase 2 would contain the price for charging from 1:00AM - 2:00AM, phrase 3 would be'  
                    'for 2:00 -3:00 AM, and so on until phrase 24 would describe the price for'  
                    'charging from 11:00PM -12:00AM. This means that phrases 1 through 24 would describe the'  
                    'price for charging during each successive hour of one day. Note'  
                    'that all 24 phrases from phrase 1 to phrase 24 must include'  
                    'a price for that hour (no N/A values should appear). Additionally, pay close attention'  
                    'to transition times between different prices. For example, if the price changes at'  
                    '2:00 PM, ensure the new price is applied to the 2:00 PM - 3:00 PM'  
                    'period. Be careful not to mistakenly apply the new 2:00 PM price to the 1:00 PM'  
                    '- 2:00 PM period. Additionally, for time intervals like 10:00 AM to 1:00 PM, be' 
                    'mindful that the time period spans both the AM and PM designations.'  
                    'For example,'  
                    '"$0.48 per kWh, 12:00AM - 6:00AM $0.60 per kWh, 6:00AM - 10:00AM $0.69 per kWh,'  
                    '10:00AM - 9:00PM $0.60 per kWh, 9:00PM - 11:00PM $0.48 per kWh, 11:00PM - 12:00AM"'  
                    '-> $0.48 per kWh | $0.48 per kWh | $0.48 per kWh | $0.48 per kWh | $0.48 per kWh |'  
                    '$0.48 per kWh | $0.60 per kWh | $0.60 per kWh | $0.60 per kWh | $0.60 per kWh | $0.69'  
                    'per kWh | $0.69 per kWh | $0.69 per kWh | $0.69 per kWh | $0.69 per kWh | $0.69'  
                    'per kWh | $0.69 per kWh | $0.69 per kWh | $0.69 per kWh | $0.69 per kWh | $0.69'  
                    'per kWh | $0.60 per kWh | $0.60 per kWh | $0.48 per kWh'
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
                phrases = output.split("|")

                # Update the correct row in the DataFrame
                for phrase, column in zip(phrases, column_list):
                    df1.at[start + j, column] = str(phrase)

        except Exception as e:
            print(f"Error processing batch starting at record {start}: {e}")
            # In case of error, mark the entire batch with error flags
            for k in range(start, end):
                for column in column_list:
                    df1.at[k, column] = -1

    return df1

def time_extraction(df1):
    # CLEAN DF1 OF ALL ROWS THAT ARE NOT THE RIGHT PRICE SCHEME
    df1 = df1[df1['Charging Scheme'].str.contains('time', na=False)].reset_index(drop=True)

    # RUN THE GPT API WITH YOUR CHOSEN FILE TYPE
    column = 'Time Price'
    df1[column] = None
    df1[column] = df1[column].astype(object)
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
                    'I will give you an input. Write a total of 1 phrase.'
                    'Using the data written in the "Pricing" , "Plug More Details" , "Charging Provider", and "Charging Scheme" columns,'
                    'This new phrase should be the specific price per hour to charge formatted as "$[price] per hour". For example,'  
                    'Statement = "$2.00/hour" -> $2.00 per hour AND Statement = "$0.10 per minute" -> $6.00 per hour'
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

                # Extract the output from the API response & store
                phrase = response_json['choices'][0]['message']['content']
                df1.at[start + j, column] = str(phrase)

        except Exception as e:
            print(f"Error processing batch starting at record {start}: {e}")
            # In case of error, mark the entire batch with error flags
            for k in range(start, end):
                df1.at[k, column] = -1

    return df1

def tiered_kWh_extraction(df1):
    # CLEAN DF1 OF ALL ROWS THAT ARE NOT THE RIGHT PRICE SCHEME
    df1 = df1[df1['Charging Scheme'].str.contains('tiered-kWh', na=False)].reset_index(drop=True)

    # RUN THE GPT API WITH YOUR CHOSEN FILE TYPE
    column_list = ['Tier 1 Price (kWh)', 'Tier 1 kWh Limit', 'Tier 2 Price (kWh)', 'Tier 2 kWh Limit', 
                   'Tier 3 Price (kWh)', 'Tier 3 kWh Limit', 'Tier 4 Price (kWh)', 'Tier 4 kWh Limit']
    for column in column_list:
        df1[column] = None
        df1[column] = df1[column].astype(object)
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
                    'I will give you an input. Write a total of 8 phrases, with each individual phrase separated by |.'
                    'Using the data written in the "Pricing", "Plug More Details" , "Charging Provider", and "Charging Scheme" columns,'
                    'phrase 1 should be the price per kWh to charge for the first tier of kWh. This is typically indicated by language like'
                    '"for the first __ kWh" or "up to __ kWh." Phrase 2 should be the maximum limit of kWh for the first tier of charging, formatted'
                    'as "__ kWh" where __ is the maximum kWh limit.'
                    'Phrases 3 through 8 should repeat the same format of phrases 1 and 2 for each successive tier, such that phrases 3 and 4'
                    'represent tier 2, phrases 5 and 6 represent tier 3, and phrases 7 and 8 represent tier 4. If there are less than 4 tiers,'
                    'write "N/A" as the phrase for all of the phrases where the tier does not exist. Note that if there is no maximum kWh limit'
                    'for the tier, you should write "unlimited" for the maximum limit for that tier and then "N/A" for all subsequent phrases.'
                    'This new phrase should be the specific price per kWh to charge formatted as "$[price] per kWh". For example,'  
                    '"$0.50/kWh for the first 10 kWh, then $0.25/kWh" -> $0.50 per kWh | 10 kWh | $0.25 per kWh | unlimited | N/A | N/A | N/A | N/A'
                    '"$0.50/kWh for 0-10 kWh, $0.30/kWh for 10-25 kWh, $0.25/kWh for 25-40 kWh, then $0.15/kWh" -> $0.50 per kWh | 10 kWh | '
                    '$0.30 per kWh | 25 kWh | $0.25 per kWh | 40 kWh | $0.15 per kWh | unlimited'
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
                phrases = output.split("|")

                # Update the correct row in the DataFrame
                for phrase, column in zip(phrases, column_list):
                    df1.at[start + j, column] = str(phrase)

        except Exception as e:
            print(f"Error processing batch starting at record {start}: {e}")
            # In case of error, mark the entire batch with error flags
            for k in range(start, end):
                for column in column_list:
                    df1.at[k, column] = -1

    return df1

def tiered_time_extraction(df1):
    # CLEAN DF1 OF ALL ROWS THAT ARE NOT THE RIGHT PRICE SCHEME
    df1 = df1[df1['Charging Scheme'].str.contains('tiered-time', na=False)].reset_index(drop=True)

   # RUN THE GPT API WITH YOUR CHOSEN FILE TYPE
    column_list = ['Tier 1 Price (time)', 'Tier 1 Time Limit', 'Tier 2 Price (time)', 'Tier 2 Time Limit', 
                   'Tier 3 Price (time)', 'Tier 3 Time Limit', 'Tier 4 Price (time)', 'Tier 4 Time Limit']
    for column in column_list:
        df1[column] = None
        df1[column] = df1[column].astype(object)
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
                    'I will give you an input. Write a total of 8 phrases, with each individual phrase separated by |.'
                    'Using the data written in the "Pricing", "Plug More Details" , "Charging Provider", and "Charging Scheme" columns,'
                    'phrase 1 should be the price per hour to charge for the first tier of hour. This is typically indicated by language like'
                    '"for the first __ hours" or "up to __ hour." Phrase 2 should be the maximum limit of hour for the first tier of charging, formatted'
                    'as "__ hour" where __ is the maximum hour limit.'
                    'Phrases 3 through 8 should repeat the same format of phrases 1 and 2 for each successive tier, such that phrases 3 and 4'
                    'represent tier 2, phrases 5 and 6 represent tier 3, and phrases 7 and 8 represent tier 4. If there are less than 4 tiers,'
                    'write "N/A" as the phrase for all of the phrases where the tier does not exist. Note that if there is no maximum hour limit'
                    'for the tier, you should write "unlimited" for the maximum limit for that tier and then "N/A" for all subsequent phrases.'
                    'This new phrase should be the specific price per hour to charge formatted as "$[price] per hour". For example,'  
                    '"$0.50/hour for the first 10 hour, then $0.25/hour" -> $0.50 per hour | 10 hour | $0.25 per hour | unlimited | N/A | N/A | N/A | N/A'
                    '"$0.50/hour for 0-10 hour, $0.30/hour for 10-25 hour, $0.25/hour for 25-40 hour, then $0.15/hour" -> $0.50 per hour | 10 hour | '
                    '$0.30 per hour | 25 hour | $0.25 per hour | 40 hour | $0.15 per hour | unlimited'
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
                phrases = output.split("|")

                # Update the correct row in the DataFrame
                for phrase, column in zip(phrases, column_list):
                    df1.at[start + j, column] = str(phrase)

        except Exception as e:
            print(f"Error processing batch starting at record {start}: {e}")
            # In case of error, mark the entire batch with error flags
            for k in range(start, end):
                for column in column_list:
                    df1.at[k, column] = -1

    return df1

def price_combination(preliminary_GPT_name, price_extraction_GPT_name):
    df1 = run_GPT(preliminary_GPT_name)

    # Run the extractions for each of the price scheme types
    df_energy = energy_extraction(df1)
    df_TOU = TOU_extraction(df1)
    df_time = time_extraction(df1)
    df_tiered_kWh = tiered_kWh_extraction(df1)
    df_tiered_time = tiered_time_extraction(df1)

    # List of dataframes
    # Identify overlapping columns
    # common_columns = set(df_TOU.columns) & set(df_time.columns) - {'Station ID'}

    # Drop overlapping columns in each dataframe
    dataframes = [df_energy, df_TOU, df_time, df_tiered_kWh, df_tiered_time]
    merged_df = dataframes[0]
    
    # Iterate through the remaining dataframes [NEEDS TO BE TESTD FURTHER]
    for df in dataframes[1:]:
        # Merge with custom suffixes
        merged_df = pd.merge(merged_df, df, on=['Station ID'], how='outer', suffixes=('', '_dup'))

        # Handle duplicate columns created during the merge
        for col in merged_df.columns:
            if col.endswith('_dup'):
                original_col = col.replace('_dup', '')  # Get the original column name
                if original_col in merged_df.columns:
                    # Combine the duplicate columns (prefer non-NaN values)
                    merged_df[original_col] = merged_df[original_col].combine_first(merged_df[col])
                # Drop the duplicate column
                merged_df = merged_df.drop(columns=[col])

    # Store the updated DataFrame as JSON lines in memory
    jsonl_data_in_memory = merged_df.to_json(orient='records', lines=True).splitlines()
    data = [json.loads(line) for line in jsonl_data_in_memory]
    df = pd.DataFrame(data)
    df.to_csv(price_extraction_GPT_name, index=False)
    print(f"Data successfully saved to a csv: {price_extraction_GPT_name}")

    return 'Done'

# TO RUN AN ENTIRE FOLDER
def run_folder(filepath, scraped_data_name, preliminary_GPT_name, price_extraction_GPT_name):
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
                print(price_combination(scraped_data_name, preliminary_GPT_name, price_extraction_GPT_name))
                
        except UnicodeDecodeError as e:
            print(f"Encoding error in file {file_path}: {e}")
        except Exception as e:
            print(f"An error occurred while processing the file {file_path}: {e}")
            pass