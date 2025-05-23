
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from app.langchain_handler import LangChainHandler
from app.db_handler import DBHandler




class LinkedinScraper:

    def __init__(self):
        self.jobs = []

    def scrape_job_links(self):

        KEYWORDS = ["engineering manager", "python", "AI",
                    "IT Manager"]
        SEARCH = "%20".join(KEYWORDS).replace(" ", "%20")
        WORK_TYPE = 2  # 1 = Onsite, 2=Remote, 3=hybrid
        LOCATION = "Germany"
        url = f"https://www.linkedin.com/jobs/search/?keywords={SEARCH}&location={LOCATION}&f_WT={WORK_TYPE}"
        headers = {
                "User-Agent": "Mozilla/5.0"}  # Important to avoid 403

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')


        for link in soup.find_all('a', class_='base-card__full-link'):
            job_title = link.get_text(strip=True)
            job_url = link['href']
            self.jobs.append((job_title, job_url))

    from selenium.common.exceptions import TimeoutException

    def get_job_info(self):
        print("-" * 50)
        print(
            f"Getting job info... for {len(self.jobs)} jobs")
        MATCH_THRESHOLD = 75
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)  # add timeout
        try:
            for idx, job in enumerate(self.jobs, start=1):
                job_title, job_url = job
                with DBHandler() as db:
                    if db.job_exists(job_url):
                        print(f"Job {idx} already exists, skipping")
                        continue

                print(
                    f"Getting job info for {job_title} - job_nr: {idx} / {len(self.jobs)}")
                try:
                    driver.get(job_url)
                except TimeoutException:
                    print(
                        f"Timeout loading page {job_url}, skipping job.")
                    continue

                try:
                    job_desc = WebDriverWait(driver,
                                             30).until(
                        ec.presence_of_element_located(
                            (By.CLASS_NAME,
                             'description__text')))
                    clean_text = job_desc.text.strip()
                    print(
                        f"Retrieved raw job info for {job_title}")

                    if clean_text:
                        lch = LangChainHandler()
                        match = lch.match_for_jobs(
                            clean_text)
                        print(
                            f"Initial match value: {match.match}")

                        if match.match > MATCH_THRESHOLD:
                            print(
                                f"processing with data extraction: {match.match}")
                            job_key_data = lch.extract_key_data_from_job_description(
                                external_job_description=True)
                            print(job_key_data)

                            with DBHandler() as dbh:
                                dbh.save_job_to_db(
                                    job_key_data, match,
                                    job_title, job_url)
                        else:
                            print(
                                f"Skipping job - match = {match.match} (threshold = {MATCH_THRESHOLD})")
                except Exception as e:
                    print(
                        f"Error while processing job: {e}")
        finally:
            driver.quit()
            print("-" * 50)


    def main(self):
        self.scrape_job_links()
        self.get_job_info()


if __name__ == '__main__':
    linkedin_scraper = LinkedinScraper()
    linkedin_scraper.main()
