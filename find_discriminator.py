# This file aim to find a class discriminator inside an HTML page that will be used to discriminate available (yes, presence of the discriminator) and soldout (no, absence of the discriminator).

from typing import Callable, Dict, List, Set, Tuple
from bs4 import BeautifulSoup
from selenium import webdriver
from tqdm import tqdm
from src.web_scraping import get_driver


class Tag: pass
class Infoname: str
class Infovalue: str


infoname_to_getter : Dict[Infoname, Callable[[Tag], Infovalue]] = {
    "id": lambda tag: tag["id"],
    "class": lambda tag: tuple(tag["class"]),
    "name" : lambda tag: tag.name,
    "text" : lambda tag: tag.text,
}
infoname_to_getter2 = {}
infoname_to_getter3 = {}
for infoname1, getter1 in infoname_to_getter.items():
    # Add combination of 2
    for infoname2, getter2 in infoname_to_getter.items():
        if infoname1 == infoname2:
            continue
        infoname_to_getter2[f"{infoname1}_{infoname2}"] = lambda tag, getter1=getter1, getter2=getter2: (getter1(tag), getter2(tag))
        # Add combination of 3
        for infoname3, getter3 in infoname_to_getter.items():
            if infoname1 == infoname3 or infoname2 == infoname3:
                continue
            infoname_to_getter3[f"{infoname1}_{infoname2}_{infoname3}"] = lambda tag, getter1=getter1, getter2=getter2, getter3=getter3: (getter1(tag), getter2(tag), getter3(tag))
infoname_to_getter.update(infoname_to_getter2)
infoname_to_getter.update(infoname_to_getter3)

def get_infos_from_tag(tag : Tag) -> List[Infovalue]:
    """Get the all the infovalues from a tag. Infovalues are the value of a certain tag according to a certain infoname.
    Infovalues contain the infoname in their name, so that we can distinguish them.

    Args:
        tag (Tag): the tag to get the infovalues from, a tag represent a html tag from the BeautifulSoup library

    Returns:
        List[Infovalue]: the list of infovalues contained in the tag
    """
    return [f"{infoname}_{getter(tag)}" for infoname, getter in infoname_to_getter.items()]

def get_set_of_identifiers_from_url(url : str, driver : webdriver.Firefox) -> Set[str]:
    """Get the set of identifiers that we can observe in the url. Identifiers are the (user destined) repr of a criteria (such as : "id is 'checkoutbutton' and name is 'div'")

    Args:
        url (str): the url of the page
        driver (webdriver.Firefox): the webdriver to use

    Returns:
        Set[str]: the set of identifiers that we can observe in the url
    """
    driver.get(url)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    tags = soup.find_all(id=True, class_=True)   # list of tags, each of which has a class attribute of type List[str]
    identifiers = sum([get_infos_from_tag(tag) for tag in tags], [])
    identifiers = set(identifiers)
    return identifiers



if __name__ == "__main__":
    print("Getting driver...")
    driver = get_driver()

    print("Loading soldout urls...")
    with open("data/soldout_urls.txt", "r") as f:
        soldout_urls = f.readlines()
        soldout_urls = set(string.strip() for string in soldout_urls)
        soldout_urls = set(string for string in soldout_urls if string != "")
        soldout_list_of_identifiers = [get_set_of_identifiers_from_url(url, driver) for url in soldout_urls]
        n_soldout_urls = len(soldout_list_of_identifiers)
    print(f"Loaded {n_soldout_urls} soldout urls.")

    print("Loading available urls...")
    with open("data/available_urls.txt", "r") as f:
        available_urls = f.readlines()
        available_urls = set(string.strip() for string in available_urls)
        available_urls = set(string for string in available_urls if string != "")
        available_list_of_identifiers_set = [get_set_of_identifiers_from_url(url, driver) for url in available_urls]
        n_available_urls = len(available_list_of_identifiers_set)
    print(f"Loaded {n_available_urls} available urls.")

    print("Computing scores for each classname...")
    identifiers_to_scores : Dict[Tuple[str], Tuple[float, float]] = {}
    # The first component denotes the number of times the classname appear in an available url's set of classnames, so its 
    # The second component denotes the number of times the classname appear in a soldout url's set of classnames, so it is True Positive + False Negative
    # We want to find the component that minimize abs(first - second)
    for identifier_set in tqdm(available_list_of_identifiers_set, desc="Available urls"):
        for identifier in identifier_set:
            if identifier in identifiers_to_scores:
                identifiers_to_scores[identifier] = (identifiers_to_scores[identifier][0] + 1, identifiers_to_scores[identifier][1])
            else:
                identifiers_to_scores[identifier] = (1, 0)
    for identifier_set in tqdm(soldout_list_of_identifiers, desc="Soldout urls"):
        for identifier in identifier_set:
            if identifier in identifiers_to_scores:
                identifiers_to_scores[identifier] = (identifiers_to_scores[identifier][0], identifiers_to_scores[identifier][1] + 1)
            else:
                identifiers_to_scores[identifier] = (0, 1)
    
    #Printing the best scores according to our criteria
    print("Best scores:")
    best_scores = sorted(identifiers_to_scores.items(), key=lambda x: abs(x[1][0] - x[1][1]), reverse=True)
    for i in range(min(10, len(best_scores))):
        identifier, (available_detected, soldout_detected) = best_scores[i]
        print(f"N°{i+1}: {identifier} with {available_detected}/{n_available_urls} available urls and {soldout_detected}/{n_soldout_urls} soldout urls")