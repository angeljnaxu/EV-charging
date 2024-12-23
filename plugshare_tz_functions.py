# Import libraries
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
from datetime import datetime, date
from bs4 import BeautifulSoup
import pandas as pd
import re
import glob

from selenium import webdriver

# HELPER FUNCTIONS FOR WEB SCRAPING
def get_true_false(container):
    try:
        result = False if container.get('aria-hidden') == 'true' else True
    except:
        result = False
    return result

def get_text_aria_na(container):
    try:
        result = [p.find(attrs={'aria-hidden':'false'}).getText() for p in container]
    except:
        result = None
    return result

def get_text_na(container):
    try:
        result = [p.getText() for p in container]
    except:
        result = None
    return result

# Helper function for disaggregating data by data time of day
def get_part_of_day(h):
    return (
        "MorningRush"
        if 8 <= h <= 11
        else "OffPeak"
        if 12 <= h <= 16
        else "EveningRush"
        if 17 <= h <= 20
        else "NA"
    )


# MAIN WEB SCRAPING FUNCTION
# timezone: lowercase string (e.g. 'eastern')
# timezone_info: timezone object from pytz library (e.g. pytz.timezone('America/New York') would be Eastern time)
# filepath: the path to the folder in which the EV_Charging repository was cloned

def get_tz_plugshare(timezone, timezone_info, filepath):
    print(timezone, timezone_info)
    time_of_day = get_part_of_day(datetime.now().hour)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--incognito')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_argument('--allow-insecure-localhost')

    #IMPORTANT: change line 70 if you need to direct to a different filepath
    # file = open('Summer24_' + str(timezone) + '.txt', mode= 'r')
    
    file = open('/Users/salataintern/Desktop/EV-Charging/Summer24_ID_Lists/summer_ids_unrestricted_nodealers.txt', mode='r')
    location_ids = file.readlines()
    count = 0
    browser = None

    for location in location_ids:
        try:
            if count % 100 == 0:
                if browser:
                    browser.quit()
                browser = webdriver.Chrome(options=chrome_options)
            if not browser:
                browser = webdriver.Chrome(options=chrome_options)
            browser.get("https://www.plugshare.com/location/" + location.strip()[:-4])
            #browser.get("https://www.plugshare.com/location/"+ location)
            time.sleep(1)

        except Exception as e:
            print(e)
            print("x")

        try: 
            interstate = int(location.strip()[-2:])
            print(interstate)

            wait = WebDriverWait(browser, 500)
            general_info_element = wait.until(EC.presence_of_element_located((By.ID, "info")))
            general_info = general_info_element.get_attribute('innerHTML')

            location_details_element = wait.until(EC.presence_of_element_located((By.ID, "location-details")))
            charger_element = wait.until(EC.presence_of_element_located((By.ID, "connectors")))
            realtime_element = wait.until(EC.presence_of_element_located((By.ID, "checkins")))

            general_info = browser.find_element(By.ID, "info").get_attribute('innerHTML')
            general_soup = BeautifulSoup(browser.page_source, 'html.parser')
            
            location_info = location_details_element.get_attribute('innerHTML') 
            location_soup = BeautifulSoup(location_info, 'html.parser')

            charger_info = charger_element.get_attribute('innerHTML')
            charger_soup = BeautifulSoup(charger_info, 'html.parser')
            
            realtime_info = realtime_element.get_attribute('innerHTML')
            realtime_soup = BeautifulSoup(realtime_info, 'html.parser')

            general_info = [p.getText() for p in general_soup.find_all(class_='content')],
            
            status_list = []
            for p in charger_soup.find_all(class_="status-dots"):
                for q in p.find_all("span"):
                    status_list.append(q.getText())  
            
            type_lst = get_text_na(charger_soup.find_all(class_="plug-name ng-binding"))
            plug_totals = get_text_na(charger_soup.find_all(class_="plug-count ng-binding"))
            plug_totals = list(map(int, re.findall(r'\d+', str(plug_totals))))

            plug_networks = [p.find(attrs={'aria-hidden':'false'}).getText() for p in charger_soup.find_all(class_="networks")]
            
            status_list = [' '.join(x) for x in zip(status_list[0::2], status_list[1::2])]
            status_list = [', '.join(x) for x in zip(status_list[0::3], status_list[1::3], status_list[2::3])]
            data_available = [False if i == '0 Available, 0 In Use, 0 Unavailable' else True for i in status_list]

            #initialize wattage variable here
            wattage = get_text_na(charger_soup.find_all(class_="plug-power ng-binding"))

            #convert to an upper limit for wattage
            cleaned_wattage = ''.join(char if char.isdigit() or char in ' -' else ' ' for char in wattage)
            parts = cleaned_wattage.split()
            upper_limit_wattage = int(parts[-1]) if parts else None

            type_status_match = pd.DataFrame({'Type': type_lst, 'Wattage': upper_limit_wattage, 'Plug Totals':plug_totals, 'Networks': plug_networks, 'Plug Status': status_list})
            #initialize wattage variable here
            wattage = get_text_na(charger_soup.find_all(class_="plug-power ng-binding"))

            #convert to an upper limit for wattage
            cleaned_wattage = ''.join(char if char.isdigit() or char in ' -' else ' ' for char in wattage)
            parts = cleaned_wattage.split()
            upper_limit_wattage = int(parts[-1]) if parts else None

            type_status_match = pd.DataFrame({'Type': type_lst, 'Wattage': upper_limit_wattage, 'Plug Totals':plug_totals, 'Networks': plug_networks, 'Plug Status': status_list})

            total_L2 = 0
            total_L2_realtime_avail = 0
            total_L3 = 0
            total_L3_realtime_avail = 0

            for index, row in type_status_match.iterrows():
                if row['Type'] == 'J-1772':
                    total_L2 += row['Plug Totals']
                    if row['Plug Status'] == '0 Available, 0 In Use, 0 Unavailable':
                        pass
                    else:
                        total_L2_realtime_avail += row['Plug Totals']
                else:
                    total_L3 += row['Plug Totals']
                    if row['Plug Status'] == '0 Available, 0 In Use, 0 Unavailable':
                        pass
                    else:
                        total_L3_realtime_avail += row['Plug Totals']
            
            under_repair = get_true_false(location_soup.find(class_="repair"))
            tesla_only = get_true_false(location_soup.find(class_="access"))
            restricted =  get_true_false(location_soup.find(class_="restricted"))
            site_type = get_text_na(location_soup.find(class_="poi-name ng-binding"))

            #Collecting pricing pop-up
            browser.execute_script("arguments[0].click();", browser.find_element(By.XPATH, '//*[@id="dialogContent_authenticate"]/button'))
            
            more_details = browser.find_element(By.XPATH, '//*[@id="connectors"]/div[2]/span')
            browser.execute_script("arguments[0].scrollIntoView();", more_details)
            browser.execute_script("arguments[0].click();", more_details)
            
            station_details_element = wait.until(EC.presence_of_element_located((By.ID, "dialogContent_stations")))
            station_info = station_details_element.get_attribute('innerHTML')
            station_soup = BeautifulSoup(station_info, 'html.parser')

            plug_outlets = []
            plug_details = []

            for p in station_soup.find_all(class_="station ng-scope"):
                plug_outlets.clear()
                plug_cost_element = p.find(class_="content")
                plug_cost = plug_cost_element.getText()[:-27] if plug_cost_element else "No cost available"

                for outlet in p.find_all(class_="box ng-scope"):
                    plug_name_element = outlet.find(class_="name ng-binding")
                    plug_power_element = outlet.find_all(class_="ng-binding")[1]
                    
                    plug_name = plug_name_element.getText() if plug_name_element else "Unknown name"
                    plug_power = plug_power_element.getText() if plug_power_element else "Unknown power"
                    
                    plug_outlets.append(f"{plug_name} ({plug_power})")
                
                plug_details.append(f"{plug_cost}: {', '.join(plug_outlets)}")

            try:
                pricing_info =  general_info[0][3]
            except:
                pricing_info = None
            try:
                hours_info = general_info[0][-2]
            except:
                hours_info = None
            try:
                description = general_info[0][-1]
            except:
                description = None

            info = {
                "Data Collection Datetime": datetime.now(timezone_info),
                "Interstate": interstate,
                "Station ID": location.strip(),
                "Station Name": location_soup.find(class_='display-title').getText(), 
                "Station Type": site_type,
                "Station Info": general_info[0],
                "Pricing Info": pricing_info,
                "Hours": hours_info,
                "Description": description,
                "Under Repair": under_repair,
                "Tesla Drivers Only": tesla_only,        
                "Restricted": restricted,        
                
                "Type": type_lst,
                "Number of Plugs": get_text_na(charger_soup.find_all(class_="plug-count ng-binding")),
                "Wattage": wattage,
                "Plug Status": status_list,
                "Real Time Data Availability": data_available,

                "Total L2 Plugs": total_L2,
                "Total L3 Plugs": total_L3,
                
                "L2 Plugs with Real Time Data": total_L2_realtime_avail,
                "L3 Plugs with Real Time Data": total_L3_realtime_avail,
                "Networked": [p.find(attrs={'aria-hidden':'false'}).getText() for p in charger_soup.find_all(class_="networks")],
            
                "Plug More Details": plug_details,

                "Last Checkin Date": realtime_soup.find(class_='date ng-binding'),
                "Last Checkin Comment": realtime_soup.find(class_='comment ng-binding basic')
                }
        except Exception as e:
            print(e)
            info = {
                "Data Collection Datetime": datetime.now(timezone_info),
                "Interstate": "NA",
                "Station ID": location.strip(),
                "Station Name": "NA", 
                "Station Type": "NA",
                "Station Info": "NA",
                "Pricing Info": "NA",
                "Hours": "NA",
                "Description": "NA",
                "Under Repair": "NA",
                "Tesla Drivers Only": "NA",        
                "Restricted": "NA",        
                
                "Type": "NA",
                "Number of Plugs": "NA",
                "Wattage": "NA",
                "Plug Status": "NA",
                "Real Time Data Availability": "NA",

                "Total L2 Plugs": "NA",
                "Total L3 Plugs": "NA",
                
                "L2 Plugs with Real Time Data": "NA",
                "L3 Plugs with Real Time Data": "NA",
                "Networked": "NA",

                "Plug More Details": "NA",
            
                "Last Checkin Date": "NA",
                "Last Checkin Comment": "NA"
            }

        station_data = pd.DataFrame([info])
        if count == 0:
            station_data.to_csv('{}/raw_data_runs/'.format(filepath) + str(timezone) + '_plugshare_scrape_' + str(date.today()) + '_' + time_of_day + '.csv')
            count += 1
        else:
            station_data.to_csv('{}/raw_data_runs/'.format(filepath) + str(timezone) + '_plugshare_scrape_' + str(date.today()) + '_' + time_of_day + '.csv', mode='a', header=False)
            count += 1
        print(count)
        print("timezone run: successfully gathered info for site " + location)

    return "Run for Timezone" + str(timezone) + " " + str(datetime.now())
