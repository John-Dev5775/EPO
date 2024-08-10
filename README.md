
---

# Web Scraping Script for EPO Patent Data

## Overview

This Python script uses Selenium to scrape patent data from the European Patent Office (EPO) publication server. It navigates through pages, clicks on "Register" links, and extracts details about patents, saving the results to a MongoDB database.

## Prerequisites

Before running the script, ensure you have the following installed:

- **Python 3.x**: The script is written in Python.
- **Selenium**: For browser automation.
- **MongoDB**: For storing scraped data.
- **ChromeDriver**: For controlling the Chrome browser.

### Install Required Python Packages

You can install the required Python packages using pip:

```bash
pip install selenium pymongo
```

## Setup

1. **MongoDB Connection**

   Replace the MongoDB URI in the script with your own MongoDB URI:

   ```python
   MONGO_URI = "mongodb+srv://<username>:<password>@cluster0.6q8pj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
   ```

2. **ChromeDriver Path**

   Ensure that `chrome_driver_path` in the script points to the location of your `chromedriver` executable:

   ```python
   chrome_driver_path = os.path.join(os.path.dirname(__file__), 'chromedriver')
   ```

   You can also specify the full path to the `chromedriver` executable if it's not in the same directory.

## Running the Script

Run the script from the command line:

```bash
python script_name.py
```

Replace `script_name.py` with the name of your Python script file.

## How It Works

1. **Initialization**: The script initializes the Chrome browser and connects to MongoDB.

2. **Navigate to EPO Website**: Opens the EPO publication server website.

3. **Click Button**: Clicks a button to start the search.

4. **Process Links**: For each page:
   - Handles Cloudflare verification if present.
   - Extracts patent details from each register page.
   - Saves the page HTML and extracted data to MongoDB.

5. **Pagination**: Clicks the "Next Page" button to continue scraping through subsequent pages.

6. **Completion**: Closes the browser once all pages are processed.

## Features

- **Retries on Failure**: Retries operations up to 3 times if they fail.
- **Cloudflare Handling**: Automatically handles Cloudflare human verification if encountered.
- **Data Storage**: Saves patent details in a MongoDB collection.
- **HTML Saving**: Optionally saves the HTML content of each page for reference.

## Troubleshooting

- **Cloudflare Verification**: If the script fails to bypass Cloudflare, ensure the correct XPath is used for the checkbox. The script assumes Cloudflare uses a checkbox with a specific XPath; this may vary.
- **Element Not Found**: Adjust XPaths in the script if the structure of the web page changes.

## License

This script is provided as-is. You are free to modify and use it for personal or educational purposes.

---
