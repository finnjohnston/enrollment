import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException
import re

class CourseScraper:
    """
    Scrapes all courses from the Vanderbilt undergraduate catalog.
    """

    def __init__(self, chromedriver_path="/opt/homebrew/bin/chromedriver"):
        self.driver = self.create_driver(chromedriver_path)

    def create_driver(self, chromedriver_path):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")
        service = Service(chromedriver_path)
        return webdriver.Chrome(service=service, options=chrome_options)

    def save_progress(self, data, filename="scraping_progress.json"):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Progress saved to {filename}")

    def load_progress(self, filename="scraping_progress.json"):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return None

    def get_subjects(self, max_retries=3):
        for attempt in range(max_retries):
            try:
                url = "https://www.vanderbilt.edu/catalogs/kuali/undergraduate-24-25.php#/courses"
                self.driver.get(url)
                wait = WebDriverWait(self.driver, 20)
                main_container = wait.until(EC.presence_of_element_located((By.ID, "kuali-catalog-main")))
                last_height = self.driver.execute_script("return document.body.scrollHeight")

                while True:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                subject_items = self.driver.find_elements(By.CSS_SELECTOR, "li")
                print(f"Found {len(subject_items)} total list items")

                subjects = []
                for i, item in enumerate(subject_items):
                    try:
                        title_element = item.find_element(By.CSS_SELECTOR, "h2[class*='style__title']")
                        subject_title = title_element.text.strip()
                        link_element = item.find_element(By.CSS_SELECTOR, "a[href*='courses'][target='_blank']")
                        course_link = link_element.get_attribute('href')

                        if subject_title and course_link:
                            subjects.append({'title': subject_title, 'course_link': course_link})
                            print(f"Subject {len(subjects)}: {subject_title}")

                    except Exception:
                        continue

                print(f"\nTotal subjects found: {len(subjects)}")
                return subjects
            
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")

                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(5)
                else:
                    raise e

    def get_course_description(self, course_url, max_retries=3):
        for attempt in range(max_retries):
            try:
                print(f"    Getting description from: {course_url} (Attempt {attempt + 1})")
                self.driver.get(course_url)

                try:
                    wait = WebDriverWait(self.driver, 15)
                    desc_div = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class^="course-view__pre"]'))
                    )
                    description = desc_div.text.strip()

                    if (len(description) > 20 and len(description) < 2000 and
                        not description.lower().startswith("arrow_back") and
                        not description.lower().startswith("back") and
                        not description.lower().startswith("academic catalog")):
                        print(f"    Found description using selector 'div[class^=\"course-view__pre\"]': {description[:100]}..." if len(description) > 100 else f"    Found description using selector 'div[class^=\"course-view__pre\"]': {description}")
                        return description
                    else:
                        print(f"    Description found but it seems like navigation or is too short/long: {description[:50]}...")
                        
                except TimeoutException:
                    print("    Timeout: Description div not found within 15 seconds.")

                except Exception as e:
                    print(f"    Error while waiting for description div: {e}")

                description_selectors = [
                    'div[class*="course-view__pre"]',
                    "div[class*='description']",
                    "div[class*='content']",
                    "div[class*='text']",
                    ".course-description",
                    ".description",
                    "p[class*='description']",
                    "div[data-testid*='description']",
                    "div[role='main'] div",
                    "main div",
                    "article div"
                ]

                for selector in description_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            potential_description = elements[0].text.strip()
                            if (len(potential_description) > 20 and 
                                len(potential_description) < 2000 and
                                not potential_description.lower().startswith("arrow_back") and
                                not potential_description.lower().startswith("back") and
                                not potential_description.lower().startswith("academic catalog")):
                                print(f"    Found description using selector '{selector}': {potential_description[:100]}..." if len(potential_description) > 100 else f"    Found description using selector '{selector}': {potential_description}")
                                return potential_description
                            else:
                                print(f"    Selector '{selector}' found text but it seems like navigation or is too short/long: {potential_description[:50]}...")

                    except Exception as e:
                        print(f"    Selector '{selector}' failed: {e}")
                        continue

                print(f"    No valid description found for course")
                return "No description available"
            
            except Exception as e:
                print(f"    Error getting description (Attempt {attempt + 1}): {e}")

                if attempt < max_retries - 1:
                    print("    Retrying...")
                else:
                    print(f"    Failed to get description after {max_retries} attempts")
                    return "Description unavailable"
                
        return "Description unavailable"

    def extract_course_code_and_title(self, course_title):
        if ' - ' in course_title:
            parts = course_title.split(' - ', 1)
            course_code = parts[0].strip()
            clean_title = parts[1].strip()
            return course_code, clean_title
        else:
            code_match = re.match(r'^([A-Z]+\d+[A-Z]*\d*)', course_title)
            if code_match:
                course_code = code_match.group(1)
                clean_title = course_title[len(course_code):].strip(' -')
                return course_code, clean_title
            else:
                return course_title, course_title

    def scrape_subject_courses(self, subject, max_retries=3):
        for attempt in range(max_retries):
            try:
                print(f"Processing subject: {subject['title']} (Attempt {attempt + 1})")
                self.driver.get(subject['course_link'])
                time.sleep(3)
                course_wait = WebDriverWait(self.driver, 15)
                course_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li")))
                print(f"  Scrolling to load all courses for {subject['title']}...")
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                scroll_attempts = 0
                max_scroll_attempts = 20

                while scroll_attempts < max_scroll_attempts:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                    scroll_attempts += 1

                print(f"  Finished scrolling for {subject['title']}, collecting courses...")

                course_links_and_titles = []
                course_list_items = self.driver.find_elements(By.CSS_SELECTOR, "li")
                print(f"  Found {len(course_list_items)} list items to examine")

                for i, li_element in enumerate(course_list_items):
                    try:
                        link_element = li_element.find_element(By.CSS_SELECTOR, "h3 a")
                        course_title = link_element.text.strip()
                        course_link = link_element.get_attribute('href')
                        if course_title and course_link and ('courses/' in course_link or '#/courses' in course_link):
                            course_links_and_titles.append((course_title, course_link))
                            print(f"  Found course link: {course_title}")

                    except Exception:
                        continue

                print(f"  Collected {len(course_links_and_titles)} course links. Now getting descriptions...")

                subject_courses = []
                seen_descriptions = set()
                for course_title, course_link in course_links_and_titles:
                    print(f"  Processing course: {course_title}")
                    course_code, clean_title = self.extract_course_code_and_title(course_title)
                    description = self.get_course_description(course_link)
                    if description in seen_descriptions and description != "No description available":
                        print(f"    WARNING: Duplicate description detected for {course_title}")
                        print(f"    Description: {description[:100]}...")
                        self.driver.refresh()
                        time.sleep(2)
                        description = self.get_course_description(course_link)

                    seen_descriptions.add(description)
                    course_info = {
                        'subject': subject['title'],
                        'course_code': course_code,
                        'course_title': clean_title,
                        'full_title': course_title,
                        'course_link': course_link,
                        'description': description
                    }
                    subject_courses.append(course_info)
                    time.sleep(1)

                print(f"Found {len(subject_courses)} courses in {subject['title']}")
                return subject_courses
            
            except Exception as e:
                print(f"Error processing {subject['title']} (Attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(5)
                    if "invalid session id" in str(e).lower():
                        print("Session invalid, recreating driver...")
                        return None
                else:
                    print(f"Failed to process {subject['title']} after {max_retries} attempts")
                    return []

    def scrape_all(self):
        progress_data = self.load_progress()
        if progress_data:
            print(f"Resuming from previous session...")
            all_courses = progress_data.get('all_courses', [])
            processed_subjects = progress_data.get('processed_subjects', [])
            subjects = progress_data.get('subjects', [])
            start_index = len(processed_subjects)
        else:
            all_courses = []
            processed_subjects = []
            subjects = []
            start_index = 0
        try:
            if not subjects:
                subjects = self.get_subjects()
                self.save_progress({
                    'subjects': subjects,
                    'processed_subjects': processed_subjects,
                    'all_courses': all_courses
                })

            for i in range(start_index, len(subjects)):
                subject = subjects[i]
                if subject['title'] in processed_subjects:
                    continue
                try:
                    subject_courses = self.scrape_subject_courses(subject)
                    if subject_courses is None:
                        print("Recreating driver due to session issues...")
                        self.driver.quit()
                        self.driver = self.create_driver("/opt/homebrew/bin/chromedriver")
                        subject_courses = self.scrape_subject_courses(subject)
                    if subject_courses:
                        all_courses.extend(subject_courses)
                    processed_subjects.append(subject['title'])
                    self.save_progress({
                        'subjects': subjects,
                        'processed_subjects': processed_subjects,
                        'all_courses': all_courses
                    })
                    print(f"Progress: {len(processed_subjects)}/{len(subjects)} subjects completed")

                except WebDriverException as e:
                    print(f"WebDriver error for {subject['title']}: {e}")
                    print("Recreating driver...")
                    self.driver.quit()
                    self.driver = self.create_driver("/opt/homebrew/bin/chromedriver")
                    continue

            print(f"\n=== FINAL SUMMARY ===")
            print(f"Total subjects processed: {len(processed_subjects)}")
            print(f"Total course lists: {len(all_courses)}")
            total_courses = sum(1 for _ in all_courses)
            print(f"Total individual courses found: {total_courses}")
            self.save_progress({
                'subjects': subjects,
                'processed_subjects': processed_subjects,
                'all_courses': all_courses,
                'completed': True
            })

            with open('courses_raw.json', 'w') as f:
                json.dump(all_courses, f, indent=2)

            print("Scraping completed successfully!")
            print("Final data saved to 'courses_raw.json'")
            
        except Exception as e:
            print(f"Fatal error: {e}")
            self.save_progress({
                'subjects': subjects,
                'processed_subjects': processed_subjects,
                'all_courses': all_courses,
                'error': str(e)
            })
        finally:
            if self.driver:
                self.driver.quit()
