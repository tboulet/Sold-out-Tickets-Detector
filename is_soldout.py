import argparse

from selenium import webdriver

from src.web_scraping import url_to_detector
    
    

if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser(description='Process URL.')
    parser.add_argument('url')
    args = parser.parse_args()
    url = args.url

    # Create driver
    driver = webdriver.Firefox("driver")

    # Check if sold out
    detector = url_to_detector(url)
    if detector is None:
        print("Site not recognized")

    else:
        print(f"Site detected : {detector.get_name()}")
        if detector.is_soldout(url, driver, db_interface=None):
            print("Status : sold out")
        else:
            print("Status : available")