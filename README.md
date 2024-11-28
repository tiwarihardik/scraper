# API Documentation for Web Scraper Service

## Overview
The Web Scraper API allows users to extract structured information such as headings, links, images, metadata, and content from any publicly accessible webpage. The API is protected by a bearer token for authentication and includes a request limit reset every hour.

---

## Base URL
```plaintext
http://<your-deployment-url>
```

---

## Authentication
The API uses **Bearer Token Authentication**. Each request must include an `Authorization` header with the format:

```
Authorization: Bearer <your-token>
```

Replace `<your-token>` with the token defined in your `.env` file under `BEARER_TOKEN`.

---

## Endpoints

### 1. **Scrape Website**
Extracts information from the provided URL.

#### **Endpoint**
```http
GET /scrape
```

#### **Headers**
| Key            | Value                           |
|-----------------|---------------------------------|
| Authorization   | Bearer `<your-token>`          |

#### **Query Parameters**
| Parameter  | Type   | Description                |
|------------|--------|----------------------------|
| `url`      | string | The URL of the webpage to scrape. |

#### **Response**

##### **Success (200)**
Returns structured data from the requested URL.

**Response Body Example**
```json
{
  "status": "success",
  "headings": {
    "h1": ["Heading 1 Text"],
    "h2": ["Subheading 1", "Subheading 2"],
    "h3": [],
    "h4": [],
    "h5": [],
    "h6": []
  },
  "links_from_tags": [
    {"text": "Example Link", "href": "https://example.com"}
  ],
  "links_from_content": [
    "https://example.com"
  ],
  "images": [
    {"src": "https://example.com/image.jpg", "alt": "Example Image"}
  ],
  "metadata": {
    "description": "Example webpage description",
    "og:title": "Example Page Title"
  },
  "content": "Full text content of the webpage."
}
```

##### **Error Responses**
| Status Code | Description                     | Example Response                                                                 |
|-------------|---------------------------------|---------------------------------------------------------------------------------|
| 400         | Missing `url` parameter         | `{ "status": "error", "error": "URL parameter is required" }`                   |
| 401         | Unauthorized                    | `{ "status": "error", "error": "Unauthorized" }`                                |
| 429         | Request limit reached           | `{ "status": "error", "error": "Request limit reached" }`                       |
| 500         | Internal server error           | `{ "status": "error", "error": "Error fetching website", "details": "<details>"}` |

---

## Features
### 1. **Request Limiting**
- **Limit**: 100 requests per hour.
- **Reset**: The request count is automatically reset every hour using a background thread.

### 2. **Extracted Information**
- **Headings**: All `h1`-`h6` tags.
- **Links**:
  - From anchor tags (`<a>`).
  - Extracted from the raw content using regex.
- **Images**: Source (`src`) and alt text (`alt`) of all `<img>` tags.
- **Metadata**: `<meta>` tags such as `description`, `og:title`, etc.
- **Content**: Full text content of the webpage.

---

## Example Usage

### cURL Example
```bash
curl -X GET "http://<your-deployment-url>/scrape?url=https://example.com" \
-H "Authorization: Bearer YOUR_TOKEN"
```

### Python Example
```python
import requests

url = "http://<your-deployment-url>/scrape"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
params = {"url": "https://example.com"}

response = requests.get(url, headers=headers, params=params)
print(response.json())
```

---

## Environment Variables
The following environment variables need to be configured:

| Variable        | Description                                      |
|-----------------|--------------------------------------------------|
| `BEARER_TOKEN`  | Authentication token for the API.               |

---

## Deployment
### Prerequisites
1. Python 3.8+
2. A `.env` file with the `BEARER_TOKEN` set.

### Local Development
Run the following commands:
```bash
pip install -r requirements.txt
flask run
```

### Production
Use `gunicorn` to deploy in a production environment:
```bash
gunicorn app:app --workers=4 --bind=0.0.0.0:8000
```

---

## Notes
- This API does not bypass CAPTCHAs or access restricted/private content.
- The service adheres to the request limit to ensure fair usage and stability.
