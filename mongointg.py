from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import os
import time
import random
from pymongo import MongoClient

# MongoDB connection details
#change to your mongo URI IMPORTANT!!!!
MONGO_URI = "mongodb+srv://sleezy:HmYOFam7qYooLS9S@cluster0.6q8pj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" #change to your mongo URI IMPORTANT!!!!
client = MongoClient(MONGO_URI)
db = client['epodata']  # Use your preferred database name
collection = db['patent_details']  # Use your preferred collection name

# Path to the chromedriver executable located in the same directory as the script
chrome_driver_path = os.path.join(os.path.dirname(__file__), 'chromedriver')

# Set up Chrome options
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Comment out this line if you want to see the browser

# Initialize WebDriver
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

def click_element(element):
    """
    Function to click an element, with retries and fallback to JavaScript click if necessary.
    """
    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(element)).click()
    except WebDriverException as e:
        print(f"WebDriverException occurred. Trying JavaScript click.")
        driver.execute_script("arguments[0].click();", element)

def save_to_mongo(document):
    """
    Function to save the extracted details to MongoDB.
    """
    collection.insert_one(document)
    print(f"Saved details to MongoDB.")

def retry_operation(operation, max_retries=3, delay=5):
    """
    Retry an operation with a specified delay between attempts.
    """
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay + random.uniform(0, 5))  # Adding random jitter to delay
    raise Exception(f"Operation failed after {max_retries} attempts")

def save_html(filename):
    """
    Save the current page's HTML content to a file.
    """
    html_content = driver.page_source
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(html_content)
    print(f"Saved HTML content to {filename}")

def handle_cloudflare_verification():
    """
    Check for Cloudflare verification and handle it if present.
    """
    try:
        # Wait for the page to load and check for the verification text
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Please verify you are a human")]'))
        )
        print("Cloudflare verification page detected. Waiting for checkbox...")

        # Wait for the checkbox to be clickable and click it
        checkbox = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="qquD4"]/div/label/input'))
        )
        checkbox.click()
        print("Clicked on the Cloudflare verification checkbox.")
        
        # Wait for the page to load again after checkbox click
        WebDriverWait(driver, 120).until(
            EC.invisibility_of_element((By.XPATH, '//*[contains(text(), "Please verify you are a human")]'))
        )
        print("Cloudflare verification completed.")
        
    except TimeoutException as e:
        print(f"TimeoutException occurred during Cloudflare verification handling: {e}")
    except WebDriverException as e:
        print(f"WebDriverException occurred during Cloudflare verification handling: {e}")

def process_links():
    """
    Function to process "Register" links on the current page and extract details from each register page.
    """
    try:
        handle_cloudflare_verification()  # Handle Cloudflare verification if needed
        
        # Find all <a> elements within <td> elements where the text is "Register"
        register_links = driver.find_elements(By.XPATH, '//td[@role="cell"]//a[text()="Register"]')

        if register_links:
            original_window = driver.current_window_handle

            for index, link in enumerate(register_links):
                if index >= 20:
                    break  # Stop after processing 20 links

                # Retry getting the PDF URL
                pdf_url_xpath = f'//*[@id="root"]/div[1]/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/table/tbody/tr[{index + 1}]/td[6]/a'
                pdf_url = 'No PDF URL found'
                try:
                    def get_pdf_url():
                        pdf_url_element = driver.find_element(By.XPATH, pdf_url_xpath)
                        return pdf_url_element.get_attribute('href').strip() if pdf_url_element else 'No PDF URL found'
                    pdf_url = retry_operation(get_pdf_url)
                except Exception as e:
                    print(f"Failed to get PDF URL for index {index}: {e}")

                # Scroll the link into view
                driver.execute_script("arguments[0].scrollIntoView(true);", link)
                time.sleep(3)  # Increased time to ensure the link is in view

                # Retry clicking the link
                def click_link():
                    try:
                        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(link)).click()
                    except WebDriverException as e:
                        print(f"WebDriverException occurred. Trying JavaScript click.")
                        driver.execute_script("arguments[0].click();", link)
                try:
                    retry_operation(click_link)
                except Exception as e:
                    print(f"Failed to click on 'Register' link {index}: {e}")
                    continue  # Skip this link and move to the next one

                # Wait for the new tab to open and switch to it
                try:
                    WebDriverWait(driver, 30).until(EC.number_of_windows_to_be(2))
                    new_window = [window for window in driver.window_handles if window != original_window][0]
                    driver.switch_to.window(new_window)
                except TimeoutException as e:
                    print(f"TimeoutException while switching to new tab for link {index}: {e}")
                    driver.close()
                    driver.switch_to.window(original_window)
                    continue  # Skip this link and move to the next one

                # Save the HTML content of the new page
                save_html(f'registry_page_{index + 1}.html')

                # Wait for the new page to load
                try:
                    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, '//td[@class="t2"]')))
                except TimeoutException as e:
                    print(f"TimeoutException while waiting for page load for link {index}: {e}")
                    driver.close()
                    driver.switch_to.window(original_window)
                    continue  # Skip this link and move to the next one

                # Extract the first element with class "t2" and clean the title
                title_element = driver.find_element(By.XPATH, '//td[@class="t2"]')
                title = title_element.text.replace("[Right-click to bookmark this link]", "").strip() if title_element else 'No title found'
                
                # Extract the first 9 characters of the title for patent number
                patent_number = title[:9] if title else 'No patent number found'

                # Check if the patent_number already exists in the database
                if collection.find_one({'patent_number': patent_number}):
                    print(f"Patent number {patent_number} already exists in the database. Skipping...")
                    driver.close()
                    driver.switch_to.window(original_window)
                    continue  # Skip this link and move to the next one

                # Extract the second and third td.t3 elements
                t3_elements = driver.find_elements(By.XPATH, '//td[@class="t3"]')
                if len(t3_elements) >= 3:
                    filing_date = t3_elements[1].text.strip() if t3_elements[1].text.strip() else 'No filing date found'
                    priority_date = t3_elements[2].text.strip() if t3_elements[2].text.strip() else 'No priority date found'
                else:
                    filing_date = 'No filing date found'
                    priority_date = 'No priority date found'

                # Extract specific td.t2 elements
                t2_elements = driver.find_elements(By.XPATH, '//td[@class="t2"]')
                def get_t2_text(index, default='Not available'):
                    return t2_elements[index].text.strip() if len(t2_elements) > index else default

                # Extract additional details
                publication_date = get_t2_text(21)
                applicants = get_t2_text(3)
                inventors = get_t2_text(5)
                representatives = get_t2_text(7)
                filing_language = get_t2_text(12)
                procedural_language = get_t2_text(13)
                status = get_t2_text(1)
                ipc_classification = get_t2_text(25)
                cpc_classification = get_t2_text(26)
                c_set_classification = get_t2_text(27)
                designated_contracting_states = get_t2_text(28)
                file_destroy_date = get_t2_text(32)

                # Print extracted data and save it to MongoDB
                document = {
                    'patent_number': patent_number,
                    'title': title,
                    'priority_date': priority_date,
                    'filing_date': filing_date,
                    'publication_date': publication_date,
                    'applicants': applicants,
                    'inventors': inventors,
                    'representatives': representatives,
                    'filing_language': filing_language,
                    'procedural_language': procedural_language,
                    'status': status,
                    'ipc_classification': ipc_classification,
                    'cpc_classification': cpc_classification,
                    'c_set_classification': c_set_classification,
                    'designated_contracting_states': designated_contracting_states,
                    'file_destroy_date': file_destroy_date,
                    'pdf_url': pdf_url,
                    'timestamp': time.time()
                }
                save_to_mongo(document)

                # Close the new tab and switch back to the original window
                driver.close()
                driver.switch_to.window(original_window)
                print(f"Closed tab for 'Register' link {index + 1} and returned to the main page.")

                # Wait briefly to ensure smooth operation
                time.sleep(3)

        else:
            print("No 'Register' links found on the current page.")
            return False  # No links found

        return True  # Links found and processed

    except TimeoutException as e:
        print(f"TimeoutException occurred: {e}")
    except WebDriverException as e:
        print(f"WebDriverException occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return False  # Error occurred

def main():
    """
    Main function to handle pagination and link processing.
    """
    driver.get("https://data.epo.org/publication-server/?lg=en")
    
    # Wait for the page to fully load
    wait = WebDriverWait(driver, 60)  # Wait up to 60 seconds

    # Wait for the button to be clickable and then click it
    button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/div[1]/div[2]/div[2]/div/div/div/form/div[4]/button[2]')))
    button.click()

    # Wait for any potential changes after the click
    time.sleep(10)  # Increased sleep time for stability

    while True:
        # Process the current page's links
        if not process_links():
            break  # Exit loop if no links found or an error occurred

        # Check if there is a "Next Page" button and click it if available
        try:
            next_page_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/div[1]/div[2]/div[2]/div/div/div[2]/div[3]/div/div/button[3]'))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", next_page_button)
            click_element(next_page_button)
            print("Clicked on 'Next Page' button.")
            time.sleep(10)  # Increased sleep time for stability
        except TimeoutException:
            print("TimeoutException occurred while trying to click 'Next Page' button.")
            break
        except WebDriverException as e:
            print(f"WebDriverException occurred while finding 'Next Page' button: {e}")
            break

    # Close the browser
    driver.quit()

if __name__ == "__main__":
    main()
