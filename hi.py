import sys
import os
import platform
import datetime
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QFileDialog,
    QMessageBox,
)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from time import sleep

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

linux_chrome_driver_path = os.path.join(BASE_DIR, "chrome/linux/chromedriver")
linux_chrome_binary_path = os.path.join(BASE_DIR, "chrome/linux/chrome-binary/chrome")

mac_chrome_driver_path = os.path.join(BASE_DIR, "chrome/mac-x64/chromedriver")
mac_chrome_binary_path = os.path.join(
    BASE_DIR,
    "chrome/mac-x64/chrome-binary/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
)


class SERPScraperApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SERP Scraper")
        self.setGeometry(100, 100, 600, 400)

        self.initUI()

        self.csv_file_path = None
        self.system = platform.system()

    def initUI(self):
        layout = QVBoxLayout()

        # Label
        self.label = QLabel("Select the CSV file with keywords", self)
        layout.addWidget(self.label)

        # Load CSV button
        self.load_button = QPushButton("Load CSV", self)
        self.load_button.clicked.connect(self.load_csv)
        layout.addWidget(self.load_button)

        # Text box to show progress
        self.textbox = QTextEdit(self)
        self.textbox.setReadOnly(True)
        layout.addWidget(self.textbox)

        # Start scraping button
        self.start_button = QPushButton("Start Scraping", self)
        self.start_button.clicked.connect(self.start_scraping)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def load_csv(self):
        # Open file dialog to select CSV file
        options = QFileDialog.Options()
        self.csv_file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv)", options=options
        )

        if self.csv_file_path:
            self.textbox.append(f"Loaded CSV file: {self.csv_file_path}")
        else:
            self.textbox.append("No file selected.")

    def start_scraping(self):
        if not self.csv_file_path:
            QMessageBox.critical(
                self, "Error", "Please load a CSV file with keywords first."
            )
            return

        # Load keyword list from CSV
        try:
            df_kwd = pd.read_csv(self.csv_file_path, encoding="utf-8", header=None)
            kwdlist = df_kwd[0].tolist()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reading CSV file: {e}")
            return

        system = platform.system()

        if system == "Linux":
            DRIVER_PATH = linux_chrome_driver_path
            BINARY_PATH = linux_chrome_binary_path

        elif system == "Darwin":  # macOS
            DRIVER_PATH = mac_chrome_driver_path
            BINARY_PATH = mac_chrome_binary_path
        else:
            raise ValueError(f"Unsupported operating system: {system}")

        # Set up Selenium options
        op = Options()
        op.add_argument("--disable-gpu")
        op.add_argument("--disable-extensions")
        op.add_argument("--disable-dev-shm-usage")
        op.add_argument("--start-maximized")
        op.add_argument("--no-sandbox")
        op.binary_location = BINARY_PATH

        # ChromeDriver auto-update and fallback logic
        try:
            service = Service(executable_path=ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=op)
        except Exception as e:
            if self.system == "Linux":
                DRIVER_PATH = linux_chrome_driver_path
            elif self.system == "Darwin":
                DRIVER_PATH = mac_chrome_driver_path
            else:
                DRIVER_PATH = ChromeDriverManager().install()

            service = Service(executable_path=DRIVER_PATH)
            driver = webdriver.Chrome(service=service, options=op)

        # Create DataFrame for results
        df = pd.DataFrame(columns=["KWD", "順位", "タイトル", "URL"])

        # Create output folder and file
        output_folder = "output"
        os.makedirs(output_folder, exist_ok=True)
        csv_date = datetime.datetime.today().strftime("%Y%m%d")
        csv_file_name = os.path.join(output_folder, f"serps_{csv_date}.csv")

        n = 0

        # Scraping settings
        SET_FILTER0 = 3

        # Start scraping
        self.textbox.append("Starting scraping process...")
        QApplication.processEvents()

        try:
            for kwd in kwdlist:
                try:
                    SET_KWD = kwd
                    SET_TITLE = "div.yuRUbf > div > span > a > h3.LC20lb"
                    SET_URL = "div.yuRUbf > div > span > a"
                    if SET_FILTER0 == 1:
                        URL = f"https://www.google.com/search?q={SET_KWD}&oq={SET_KWD}&num=100&filter=0"
                    elif SET_FILTER0 == 2:
                        URL = f"https://www.google.com/search?q={SET_KWD}&oq={SET_KWD}&num=100"
                    else:
                        URL = f"https://www.google.com/search?q={SET_KWD}&oq={SET_KWD}"

                    driver.get(URL)
                    self.textbox.append(f"Scraping for keyword: {SET_KWD}...")
                    QApplication.processEvents()

                    # Wait for the page to load
                    while True:
                        page_source = driver.page_source
                        if "unusual traffic" not in page_source:
                            break
                        sleep(1)

                    soup = BeautifulSoup(page_source, features="html.parser")
                    SET_URLNUM = len(soup.select(SET_TITLE))

                    for i in range(SET_URLNUM):
                        D_num = i + 1
                        D_URL = soup.select(SET_URL)[i].get("href")
                        D_TITLE = soup.select(SET_TITLE)[i].string
                        df.loc[n] = [SET_KWD, D_num, D_TITLE, D_URL]
                        n += 1

                    sleep(2)

                except Exception as e:
                    self.textbox.append(f"Error processing keyword '{kwd}': {e}")
                    QApplication.processEvents()
                    continue

            df.to_csv(csv_file_name, encoding="utf-8", header=False, index=False)
            self.textbox.append(f"Scraping completed. Results saved to {csv_file_name}")
            QApplication.processEvents()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error during scraping process: {e}")
        finally:
            driver.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    scraper = SERPScraperApp()
    scraper.show()
    sys.exit(app.exec_())
