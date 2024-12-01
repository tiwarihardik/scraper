from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import re
from dotenv import load_dotenv
import os
from flask_cors import CORS
import time

# Load environment variables
load_dotenv()
app = Flask(__name__)

# Enabling CORS for all routes
CORS(app)

# Configuration
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
REQUEST_LIMIT = 100
request_count = 0
last_reset_time = time.time()
RESET_INTERVAL = 3600  # 1 hour in seconds

# Function to check bearer token
def check_bearer_token(token):
    return token == BEARER_TOKEN

# Function to reset request count every hour
def reset_request_count():
    global request_count, last_reset_time
    current_time = time.time()
    if current_time - last_reset_time >= RESET_INTERVAL:
        request_count = 0
        last_reset_time = current_time

# Function to calculate remaining reset time
def get_remaining_reset_time():
    return max(0, RESET_INTERVAL - (time.time() - last_reset_time))

# Asynchronous function to scrape data from a website
async def scrape_website(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10, headers={'User-Agent': 'LowEndAPI/1.0'}) as response:
                if response.status != 200:
                    return {'error': 'Failed to fetch the website', 'status_code': response.status}, response.status

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract headings
                headings = {f'h{i}': [tag.text.strip() for tag in soup.find_all(f'h{i}')] for i in range(1, 7)}

                # Extract links from anchor tags
                links_from_tags = [{'text': link.text.strip(), 'href': link.get('href')} for link in soup.find_all('a', href=True)]

                # Extract full content
                full_content = soup.get_text(separator='\n', strip=True)

                # Extract links from the content
                url_pattern = r'(https?://[^\s]+)'
                links_from_content = re.findall(url_pattern, full_content)

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
    except aiohttp.ClientError as e:
        return {'status': 'error', 'error': 'Error fetching website', 'details': str(e)}

@app.route('/scrape', methods=['GET'])
async def scrape():
    global request_count
    reset_request_count()

    if request_count >= REQUEST_LIMIT:
        return jsonify({'status': 'error', 'error': 'Request limit reached'}), 429

    token = request.headers.get('Authorization')
    if not token or not check_bearer_token(token.split(' ')[1]):
        return jsonify({'status': 'error', 'error': 'Unauthorized'}), 401

    url = request.args.get('url')
    if not url:
        return jsonify({'status': 'error', 'error': 'URL parameter is required'}), 400

    request_count += 1
    return jsonify(await scrape_website(url))

@app.route('/', methods=['GET'])
def status():
    reset_request_count()
    remaining_time = get_remaining_reset_time()
    return jsonify({
        'status': 'success',
        'current_request_count': request_count,
        'remaining_time_to_reset': remaining_time
    })

if __name__ == '__main__':
    # Use asyncio to run the Flask app
    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0"]
    asyncio.run(serve(app, config))
