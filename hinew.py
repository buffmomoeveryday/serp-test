from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from time import sleep
from webdriver_manager.chrome import ChromeDriverManager
import datetime
import pandas as pd
import os
import platform

# Selenium options
op = Options()
op.add_argument("--disable-gpu")
op.add_argument("--disable-extensions")
op.add_argument("--disable-dev-shm-usage")
op.add_argument("--proxy-server='direct://'")
op.add_argument("--proxy-bypass-list=*")
op.add_argument("--start-maximized")  # Open Chrome maximized
# op.add_argument("--headless")  # Uncomment if running on a server (no GUI)
op.add_argument("--no-sandbox")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


linux_chrome_driver_path = os.path.join(BASE_DIR, "chrome/linux/chromedriver")
linux_chrome_binary_path = os.path.join(BASE_DIR, "chrome/linux/chrome-binary/chrome")

mac_chrome_driver_path = os.path.join(BASE_DIR, "chrome/mac-x64/chromedriver")
mac_chrome_binary_path = os.path.join(
    BASE_DIR,
    "chrome/mac-x64/chrome-binary/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
)


system = platform.system()

if system == "Linux":
    DRIVER_PATH = linux_chrome_driver_path
    BINARY_PATH = linux_chrome_binary_path

elif system == "Darwin":  # macOS
    DRIVER_PATH = mac_chrome_driver_path
    BINARY_PATH = mac_chrome_binary_path
else:
    raise ValueError(f"Unsupported operating system: {system}")


# Set the path to the Chrome binary
op.binary_location = BINARY_PATH

# ChromeDriver auto-update
try:
    service = Service(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=op)
except Exception as e:
    driver_path = DRIVER_PATH
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=op)

# Create DataFrame
df = pd.DataFrame(columns=["KWD", "順位", "タイトル", "URL"])

# Create output folder if it doesn't exist
output_folder = "output"
os.makedirs(output_folder, exist_ok=True)

# CSV file setup
csv_date = datetime.datetime.today().strftime("%Y%m%d")
csv_file_name = os.path.join(output_folder, f"serps_{csv_date}.csv")

# Read keyword list from CSV
df_kwd = pd.read_csv("kwd.csv", encoding="utf-8", header=None)
kwdlist = df_kwd[0].tolist()

n = 0

# Settings
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
                URL = f"https://www.google.com/"
            elif SET_FILTER0 == 2:
                URL = f"https://www.google.com/"
            else:
                URL = f"https://www.google.com/"

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
                    D_URL = soup.select(SET_URL)[i].get("href")
                    D_TITLE = soup.select(SET_TITLE)[i].string
                    addrow = [SET_KWD, D_num, D_TITLE, D_URL]
                    df.loc[n] = addrow
                    n += 1
                except Exception as e:
                    print(f"Error processing result {i+1} for '{SET_KWD}': {e}")
            sleep(2)
        except Exception as e:
            print(f"Error processing keyword '{kwd}': {e}")
            continue
finally:
    df.to_csv(csv_file_name, encoding="utf-8", header=False, index=False)
    driver.quit()
