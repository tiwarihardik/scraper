from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests
import threading
import time
import re
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)

# Configuration
BEARER_TOKEN = os.getenv("BEARER_TOKEN" )
REQUEST_LIMIT = 100
request_count = 0

# Function to check bearer token
def check_bearer_token(token):
    return token == BEARER_TOKEN

# Function to extract links from content
def extract_links_from_content(content):
    # Regex pattern for URLs
    url_pattern = r'(https?://[^\s]+)'
    # Find all matches of the pattern in the content
    links = re.findall(url_pattern, content)
    return links

# Function to scrape data from a website
def scrape_website(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {'error': 'Failed to fetch the website', 'status_code': response.status_code}, response.status_code

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract headings
        headings = {f'h{i}': [tag.text.strip() for tag in soup.find_all(f'h{i}')] for i in range(1, 7)}

        # Extract links from anchor tags
        links_from_tags = [{'text': link.text.strip(), 'href': link.get('href')} for link in soup.find_all('a', href=True)]

        # Extract full content
        full_content = soup.get_text(separator='\n', strip=True)

        # Extract links from the content
        links_from_content = extract_links_from_content(full_content)

        # Extract images
        images = [{'src': img.get('src'), 'alt': img.get('alt', '')} for img in soup.find_all('img')]

        # Extract metadata
        metadata = {meta.get('name', meta.get('property', 'unknown')): meta.get('content', '')
                    for meta in soup.find_all('meta') if meta.get('content')}

        return {
            'status': 'success',
            'headings': headings,
            'links_from_tags': links_from_tags,
            'links_from_content': links_from_content,
            'images': images,
            'metadata': metadata,
            'content': full_content
        }
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'error': 'Error fetching website', 'details': str(e)}
# Background thread to reset request count every hour
def reset_request_count():
    global request_count
    while True:
        time.sleep(3600)  # Sleep for one hour
        request_count = 0
        print("Request count reset to 0")

@app.route('/scrape', methods=['GET'])
def scrape():
    global request_count
    reset_thread = threading.Thread(target=reset_request_count, daemon=True)
    reset_thread.start()
    if request_count >= REQUEST_LIMIT:
        return jsonify({'status': 'error', 'error': 'Request limit reached'}), 429

    token = request.headers.get('Authorization')
    if not token or not check_bearer_token(token.split(' ')[1]):
        return jsonify({'status': 'error', 'error': 'Unauthorized'}), 401

    url = request.args.get('url')
    if not url:
        return jsonify({'status': 'error', 'error': 'URL parameter is required'}), 400

    data = scrape_website(url)
    request_count += 1
    return jsonify(data)


'''if __name__ == '__main__':
    # Start the reset thread
    app.run()    
'''

