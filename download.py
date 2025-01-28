import platform
import os
import requests
import stat
import zipfile
import sys
from time import sleep
import platform
import os
import requests
import stat
import zipfile
import sys
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class PlatformInfo:
    """Class to handle platform and architecture detection."""

    def __init__(self):
        self.current_os = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.platform_key = self.get_platform_key()

    def get_platform_key(self):
        """Determine the platform key based on current OS and architecture."""
        if self.current_os == "linux":
            return "linux64"
        elif self.current_os == "darwin":
            return "mac-arm64" if self.architecture == "arm64" else "mac-x64"
        elif self.current_os == "windows":
            return "win64" if sys.maxsize > 2**32 else "win32"
        else:
            raise Exception(
                f"Unsupported OS/architecture: {self.current_os}/{self.architecture}"
            )


class Downloader:
    """Class to handle downloading and extracting files."""

    def __init__(self):
        self.chrome_version = "134.0.6983.0"
        self.chrome_urls = self._get_chrome_urls()
        self.chromedriver_urls = self._get_chromedriver_urls()

    def _get_chrome_urls(self):
        """Define URLs for Chrome downloads based on version."""
        return {
            "linux64": f"https://storage.googleapis.com/chrome-for-testing-public/{self.chrome_version}/linux64/chrome-linux64.zip",
            "mac-arm64": f"https://storage.googleapis.com/chrome-for-testing-public/{self.chrome_version}/mac-arm64/chrome-mac-arm64.zip",
            "mac-x64": f"https://storage.googleapis.com/chrome-for-testing-public/{self.chrome_version}/mac-x64/chrome-mac-x64.zip",
            "win32": f"https://storage.googleapis.com/chrome-for-testing-public/{self.chrome_version}/win32/chrome-win32.zip",
            "win64": f"https://storage.googleapis.com/chrome-for-testing-public/{self.chrome_version}/win64/chrome-win64.zip",
        }

    def _get_chromedriver_urls(self):
        """Define URLs for ChromeDriver downloads based on version."""
        return {
            "linux64": f"https://storage.googleapis.com/chrome-for-testing-public/{self.chrome_version}/linux64/chromedriver-linux64.zip",
            "mac-arm64": f"https://storage.googleapis.com/chrome-for-testing-public/{self.chrome_version}/mac-arm64/chromedriver-mac-arm64.zip",
            "mac-x64": f"https://storage.googleapis.com/chrome-for-testing-public/{self.chrome_version}/mac-x64/chromedriver-mac-x64.zip",
            "win32": f"https://storage.googleapis.com/chrome-for-testing-public/{self.chrome_version}/win32/chromedriver-win32.zip",
            "win64": f"https://storage.googleapis.com/chrome-for-testing-public/{self.chrome_version}/win64/chromedriver-win64.zip",
        }

    def set_executable_permission(self, file_path):
        """Set executable permission for a file."""
        if os.path.exists(file_path):
            st = os.stat(file_path)
            os.chmod(file_path, st.st_mode | stat.S_IEXEC)
            print(f"Set executable permission for {file_path}")
        else:
            print(f"File not found: {file_path}")

    def download_and_extract(self, url, extract_path, retries=3):
        """Download and extract a ZIP file."""
        zip_path = f"{extract_path}.zip"
        for attempt in range(retries):
            try:
                print(f"Downloading {url}... (Attempt {attempt+1}/{retries})")
                response = requests.get(url, stream=True)
                response.raise_for_status()

                if "application/zip" not in response.headers.get("Content-Type", ""):
                    raise ValueError("Downloaded file is not a ZIP file")

                with open(zip_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)

                print(f"Extracting {zip_path}...")
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(extract_path)

                os.remove(zip_path)

                # Set executable permissions for Unix-based systems
                for root, dirs, files in os.walk(extract_path):
                    for file in files:
                        if file in ["chrome", "chromedriver", "Google Chrome"]:
                            self.set_executable_permission(os.path.join(root, file))
                return True
            except Exception as e:
                print(f"Error: {str(e)}")
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                if attempt < retries - 1:
                    sleep(2)
        return False


class ChromeSetup:
    """Class to handle the complete setup of Chrome and ChromeDriver."""

    def __init__(self, platform_key):
        self.platform_key = platform_key
        self.downloader = Downloader()
        self.paths = self._get_paths()

    def _get_paths(self):
        """Define paths for Chrome and ChromeDriver based on platform."""
        return {
            "linux64": {
                "chrome": "./chrome-folder/chrome-linux64/chrome",
                "driver": "./chromedriver-folder/chromedriver-linux64/chromedriver",
            },
            "mac-arm64": {
                "chrome": "./chrome-folder/chrome-mac-arm64/Google Chrome.app/Contents/MacOS/Google Chrome",
                "driver": "./chromedriver-folder/chromedriver-mac-arm64/chromedriver",
            },
            "mac-x64": {
                "chrome": "./chrome-folder/chrome-mac-x64/Google Chrome.app/Contents/MacOS/Google Chrome",
                "driver": "./chromedriver-folder/chromedriver-mac-x64/chromedriver",
            },
            "win32": {
                "chrome": "./chrome-folder/chrome-win32/chrome.exe",
                "driver": "./chromedriver-folder/chromedriver-win32/chromedriver.exe",
            },
            "win64": {
                "chrome": "./chrome-folder/chrome-win64/chrome.exe",
                "driver": "./chromedriver-folder/chromedriver-win64/chromedriver.exe",
            },
        }

    def setup_chrome(self):
        """Download and extract Chrome if necessary."""
        chrome_binary = self.paths[self.platform_key]["chrome"]
        if not os.path.exists(chrome_binary):
            print("Setting up Chrome browser...")
            if self.downloader.download_and_extract(
                self.downloader.chrome_urls[self.platform_key], "./chrome-folder"
            ):
                print("Chrome setup completed successfully")
            else:
                raise RuntimeError("Failed to download Chrome")

    def setup_chromedriver(self):
        """Download and extract ChromeDriver if necessary."""
        chromedriver_path = self.paths[self.platform_key]["driver"]
        if not os.path.exists(chromedriver_path):
            print("Setting up ChromeDriver...")
            if self.downloader.download_and_extract(
                self.downloader.chromedriver_urls[self.platform_key],
                "./chromedriver-folder",
            ):
                print("ChromeDriver setup completed successfully")
            else:
                raise RuntimeError("Failed to download ChromeDriver")


# if __name__ == "__main__":
#     platform_info = PlatformInfo()
#     chrome_setup = ChromeSetup(platform_info.platform_key)

#     chrome_setup.setup_chrome()
#     chrome_setup.setup_chromedriver()


def create_selenium_driver(chrome_binary_path, chromedriver_path, options):
    """Helper function to create a Selenium WebDriver instance."""
    try:
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Error initializing ChromeDriver: {e}")
        return None
