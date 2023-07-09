# This file aim to find a class discriminator inside an HTML page that will be used to discriminate available (yes, presence of the discriminator) and soldout (no, absence of the discriminator).


from bs4 import BeautifulSoup
from src.web_scraping import get_driver


if __name__ == "__main__":

    with open("data/soldout_urls.txt", "r") as f:
        soldout_urls = f.readlines()
        soldout_urls = [string.strip() for string in soldout_urls]
        soldout_urls = [string for string in soldout_urls if string != ""]

    with open("data/available_urls.txt", "r") as f:
        available_urls = f.readlines()
        available_urls = [string.strip() for string in available_urls]
        available_urls = [string for string in available_urls if string != ""]

    driver = get_driver()

    url_available = available_urls[0]
    driver.get(url_available)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    tags_availability_candidates = soup.find_all(class_=True)

    num_candidates = len(tags_availability_candidates)
    for i, tag_av_candidate in enumerate(tags_availability_candidates):
        # Check if the candidate is a discriminator
        class_name_candidate = tag_av_candidate["class"]
        is_candidate = True
        print(f"\nChecking candidate {i+1}/{num_candidates} : {class_name_candidate}")

        # Verify the candidate tag is NOT the tags of the page
        for url in soldout_urls:
            driver.get(url)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            tags = soup.find_all(class_=True)
            classes = [tag["class"] for tag in tags]
            if class_name_candidate in classes:
                is_candidate = False
                break
        if not is_candidate:
            print(f"{class_name_candidate} is not a discriminator because it is in the soldout page {url}")
            continue

        # Verify the candidate tag is the tags of the page
        for url in available_urls:
            driver.get(url)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            tags = soup.find_all(class_=True)
            classes = [tag["class"] for tag in tags]
            if class_name_candidate not in classes:
                is_candidate = False
                break

        # Check if the candidate passed the test
        if not is_candidate:
            print(f"{class_name_candidate} is not a discriminator because it is not in the available page {url}")
            continue

        # If the candidate passed the test, it is a discriminator
        print(f"{class_name_candidate} is a discriminator !")