from abc import ABC, abstractmethod
from typing import Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
import argparse
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup


def get_driver():
    return webdriver.Firefox("driver")

def is_in_url_classes(
    url: str, 
    element: Any, 
    driver: webdriver.Firefox
):
    driver.get(url)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    tags = soup.find_all(class_=True)
    classes = [tag["class"] for tag in tags]
    return element in classes

class SoldoutDetector(ABC):
    """Abstract class for soldout detectors"""
    def __init__(self) -> None:
        super().__init__()
    @abstractmethod
    def get_name(self):
        """Get the name of the soldout detector
        """
        raise NotImplementedError("Please Implement this method")
    @abstractmethod
    def is_soldout(self, url : str, driver : webdriver.Firefox):
        """Return True if the event is soldout, False otherwise

        Args:
            url (str): the url of the event
            driver (webdriver.Firefox): the webdriver to use
        """
        raise NotImplementedError("Please Implement this method")



class TicktwebSoldoutDetector(SoldoutDetector):
    
    def get_name(self):
        return "TicketWeb"
    
    def is_soldout(self, url : str, driver : webdriver.Firefox):
        driver.get(url)
        try:
            driver.find_element(By.ID, "edp-section-tickets-heading")
            return False
        except NoSuchElementException:
            return True
    


class SeeTicketsSoldoutDetector(SoldoutDetector):
    def get_name(self):
        return "SeeTickets"
    
    def is_soldout(self, url: str, driver: webdriver.Firefox):
        
        # Tag identifier method
        return not is_in_url_classes(url, ['changeMe', 'shipping'], driver)

        # Text reading method
        driver.get(url)
        page_source = driver.page_source
        for text_of_soldout_page in [
            "Event is SOLD OUT",
            "Tickets are not available",
            "No recordsNo records",
            "Tickets available at the box office",
            ]:
            if text_of_soldout_page in page_source:
                return True
        return False


class EtixSoldoutDetector(SoldoutDetector):
    def get_name(self):
        return "Etix"
    
    def is_soldout(self, url : str, driver : webdriver.Firefox):
        driver.get(url)
        try:
            driver.find_element(By.ID, "normal-price-code")
            return False
        except NoSuchElementException:
            return True
        

        
def url_to_detector(url : str) -> SoldoutDetector:
    """This function try to extract the site name from the url, and return the corresponding SoldoutDetector object

    Args:
        url (str): the url to extract the site name from

    Returns:
        SoldoutDetector: the corresponding SoldoutDetector object
    """
    
    if "www.ticketweb.com" in url:
        return TicktwebSoldoutDetector()
    
    elif "seetickets" in url:
        return SeeTicketsSoldoutDetector()
    
    elif "etix.com" in url:
        return EtixSoldoutDetector()
    
    else:
        return None