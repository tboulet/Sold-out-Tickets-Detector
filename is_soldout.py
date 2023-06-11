from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
import argparse



def is_sold_out_ticketweb(url : str, driver : webdriver.Firefox):
    print("Checking whether tickets are sold out on Ticketweb...")
    driver.get(url)
    try:
        driver.find_element(By.ID, "edp-section-tickets-heading")
        return False
    except:
        return True
    
    

if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser(description='Process URL.')
    parser.add_argument('url')
    args = parser.parse_args()
    url = args.url

    # Create driver
    driver = webdriver.Firefox("driver")

    # Check if sold out
    print(is_sold_out_ticketweb(url, driver))