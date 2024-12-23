# EV-charging
This is my work on web scraping, data processing, and OpenAPI access for public EV charging with the Harvard Salata Institute. 

1. plugshare_tz_functions.py. This script facilitates web scraping from the Plugshare website to collect data on DC Fast Chargers on key interstates across the United States (I-95, I-5, I-90, I-80, I-10, and I-75). Code to collect additional data from the Plugshare website itself can be inserted into the main web scraping function within this script (plugshare_tz_scrape). The by-timezone scraping method in this program ensures that we can collect the data for each station at the same time local time in each run.

2. plugshare_data_processing.py. This script uses the pandas and numpy libraries to process the raw data produced by plugshare_tz_functions.py into a cleaner format to conduct analysis tasks. It takes in a csv file and uses the pandas library to reformat the data frame, outputting a new cleaned csv file.

3. GPT4_plugshare_price_scheme_functions.py. This script contains several different GPT4o prompts for each of the different types of EV charging station pricing schemes, each of which is contained within a separate function. The first function (preliminary_scheme) runs a preliminary scheme classification, where solely the Plugshare scraped data is inputted and the pricing scheme for charging is outputted by GPT4o according to the definitions given in the prompt. The subsequent functions are tailored for each specific type of pricing scheme for charging, such that GPT can extract the exact price given the scraped Plugshare data and the output from the preliminary_scheme function that states the types of prices that should be listed. 

extract_numbers(wattage_list) is a helper function to extract all the numbers from a wattage list.

filter_wattage(wattage_list) is a helper function to filter out wattages that are less than 50.

extract_plugs(plugs_list) is a helper function to extract the number of plugs from a plug list.

geoloc_data_cleaning(filepath, filename) is the main folder for processing the raw data runs. Depending on commented/uncommented lines, the function can process all IDs from all runs. If you uncomment lines 69-70, 399: only processes the IDs from the recalc list and excludes restricted. Uncomment lines 69-70, 398, Comment Line 59: only process the IDs from the recalc list. This one is required to ensure that when checking viability of runs, the 95% viability matches.

run_processing(filepath) iterates through the raw_data_runs folder and opens each internal date folder within the raw_data_runs.

run_timezone (filepath, time zones, times_of_day, dates) does data processing by the timezones/time of day/date.

clean_old_runs(filepath) cleans up the interstates data and standardizes the varying types of interstate data that was collected. Note: this function has become somewhat pointless as we are no longer looking at interstate runs. 

4. GPT4_plugshare_price_scheme.py. This script takes csv files produced by plugshare_data_processing.py and delivers a prompt to OpenAI API asking it to extract the pricing scheme from the "pricing details" and "more details" columns in multiple phrases. Each of the phrases are saved in a separate column of the pandas dataframe, and then the data is converted from a json file to a csv file. 
