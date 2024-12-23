from GPT4_plugshare_price_scheme_functions import preliminary_scheme, price_combination, run_folder

# PERSONALIZE THE INPUTS: PRELIMINARY CSV FILE GOES HERE->
scraped_data_file = "processed_runs/NOUnknowns_no_energy_TOU_sample.csv"
preliminary_scheme_file = "GPT_raw_data_runs/12-4_ChatGPT-TOU_NOUnknowns_no_energy_TOU_sample_preliminary_updatedprompt4.csv"
price_extraction_GPT_file = "GPT_raw_data_runs/12-4_ChatGPT-TOU_NOUnknowns_200stations_fast_plug_only.csv"

# only run this if you haven't gotten the preliminary schemes down yet! 
preliminary_scheme(scraped_data_file, preliminary_scheme_file)

# if trying to extract individual prices from one file
# price_combination(preliminary_scheme_file, price_extraction_GPT_file)

# Note that run_folder is still untested & needs to be fixed!