from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from time import sleep
import chromedriver_binary
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import datetime
import pandas as pd
import os
import platform
from download import PlatformInfo, Downloader, ChromeSetup, create_selenium_driver

platform_info = PlatformInfo()
chrome_setup = ChromeSetup(platform_info.platform_key)

# Set up Chrome and ChromeDriver if necessary
chrome_setup.setup_chrome()
chrome_setup.setup_chromedriver()

# Selenium options
op = Options()
op.add_argument("--disable-gpu")
op.add_argument("--disable-extensions")
op.add_argument("--disable-dev-shm-usage")
op.add_argument("--proxy-server='direct://'")
op.add_argument("--proxy-bypass-list=*")
op.add_argument("--start-maximized")
# op.add_argument("--headless")  # Uncomment if running on a server (no GUI)
op.add_argument("--no-sandbox")

# Add a unique user data directory to avoid conflicts
# user_data_dir = "./chrome_user_data"

# os.makedirs(user_data_dir, exist_ok=True)
# op.add_argument(f"--user-data-dir={user_data_dir}")

op.binary_location = chrome_setup.paths[platform_info.platform_key]["chrome"]

print(op.binary_location)
print(chrome_setup.paths[platform_info.platform_key]["chrome"])
print(chrome_setup.paths[platform_info.platform_key]["driver"])

driver = create_selenium_driver(
    chrome_binary_path=chrome_setup.paths[platform_info.platform_key]["chrome"],
    chromedriver_path=chrome_setup.paths[platform_info.platform_key]["driver"],
    options=op,
)


df = pd.DataFrame(columns=["KWD", "順位", "タイトル", "URL"])

output_folder = "output"
os.makedirs(output_folder, exist_ok=True)

csv_date = datetime.datetime.today().strftime("%Y%m%d")
csv_file_name = os.path.join(output_folder, f"serps_{csv_date}.csv")

df_kwd = pd.read_csv("kwd.csv", encoding="utf-8", header=None)
kwdlist = df_kwd[0].tolist()

n = 0

SET_URLNUM = 100
SET_FILTER0 = 3

try:
    for kwd in kwdlist:
        try:
            SET_KWD = kwd
            SET_TITLE = "div.yuRUbf > div > span > a > h3.LC20lb"
            SET_URL = "div.yuRUbf > div > span > a"
            SET_TITLE_PAA = "div.Wt5Tfe > div.yuRUbf > div > span > a > h3.LC20lb"
            SET_URL_PAA = "div.Wt5Tfe > div.yuRUbf > div > span > a"

            if SET_FILTER0 == 1:
                URL = f"https://www.google.com/search?q={SET_KWD}&oq={SET_KWD}&num=100&filter=0"
            elif SET_FILTER0 == 2:
                URL = f"https://www.google.com/search?q={SET_KWD}&oq={SET_KWD}&num=100"
            else:
                URL = f"https://www.google.com/search?q={SET_KWD}&oq={SET_KWD}"

            driver.get(URL)  # Open the page

            while True:
                page_source = driver.page_source
                if "unusual traffic" not in page_source:
                    break

                print("Network anomaly detected. Retrying in 1 second.")
                sleep(1)

            soup = BeautifulSoup(page_source, features="html.parser")

            if soup.find("div", {"class": "Wt5Tfe"}) is not None:
                soup.find("div", {"class": "Wt5Tfe"}).decompose()

            SET_URLNUM = int(len(soup.select(SET_TITLE)))
            print(SET_URLNUM)

            for i in range(SET_URLNUM):
                try:
                    D_num = i + 1
                    D_URL_element = soup.select(SET_URL)[i]
                    D_TITLE_element = soup.select(SET_TITLE)[i]

                    # Check if elements are found
                    if D_URL_element and D_TITLE_element:
                        D_URL = D_URL_element.get("href")
                        D_TITLE = D_TITLE_element.string
                        addrow = [SET_KWD, D_num, D_TITLE, D_URL]
                        df.loc[n] = addrow
                        print(df)
                        n += 1
                    else:
                        print(
                            f"Skipping result {i+1} for '{SET_KWD}' due to missing elements."
                        )
                except Exception as e:
                    print(f"Error processing result {i+1} for '{SET_KWD}': {e}")
            sleep(2)
        except Exception as e:
            print(f"Error processing keyword '{kwd}': {e}")
            continue
finally:
    if driver:
        driver.quit()

    df.to_csv(csv_file_name, encoding="utf-8", header=False, index=False)
