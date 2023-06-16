from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
import argparse
    
    


    

class SoldoutDetector(ABC):
    def __init__(self) -> None:
        super().__init__()
    @abstractmethod
    def get_name(self):
        pass
    @abstractmethod
    def is_soldout(self, url : str, driver : webdriver.Firefox):
        pass



class TicktwebSoldoutDetector(SoldoutDetector):
    def __init__(self) -> None:
        super().__init__()
    
    def get_name(self):
        return "TicketWeb"
    
    def is_soldout(self, url : str, driver : webdriver.Firefox):
        driver.get(url)
        try:
            driver.find_element(By.ID, "edp-section-tickets-heading")
            return False
        except:
            return True
    



def url_to_detector(url : str) -> SoldoutDetector:
    """This function try to extract the site name from the url, and return the corresponding SoldoutDetector object

    Args:
        url (str): the url to extract the site name from

    Returns:
        SoldoutDetector: the corresponding SoldoutDetector object
    """
    if "ticketweb" in url:
        return TicktwebSoldoutDetector()
    
    else:
        return None