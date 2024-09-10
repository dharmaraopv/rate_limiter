Here’s the updated `README.md` with the requested changes:

---

# Rate Limiter API

This project provides a FastAPI-based service for rate limiting. It allows users to configure rate limit settings and check if a specific user (identified by a unique token) is rate-limited based on those configurations.

## Features

- **Configure Rate Limiter**: Set rate limit configurations like intervals and limits.
- **Check Rate Limit**: Check if a specific user is currently rate-limited using their unique token.
- **Requests Tracking**: Supports tracking requests using either Redis or an in-memory store. This is configurable via environment settings, allowing you to choose between Redis for distributed systems or an in-memory store for simpler, local setups.

## Installation

### Prerequisites

- Python 3.x (tested on Python 3.9)
- [Redis 7.4.0](https://redis.io/download)

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/dharmaraopv/rate_limiter
   cd rate_limiter
   ```

2. Create and activate a virtual environment:
   ```bash
   python3.9 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the Redis server (if using Redis):
   ```bash
   redis-server
   ```

6. Run the application:
   a. In-memory store:
   ```bash
   ENV=in_mem uvicorn main:app --reload
   ```
   b. Redis store:
   ```bash
    ENV=redis uvicorn main:app --reload
   ```
   
7. Read the API documentation and try apis via [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## API Endpoints

### 1. Configure Rate Limiter

**POST** `/api/configure`

- **Description**: Configure rate limiter settings.
- **Request Body**: 
  - `interval`: Time window for rate limiting (e.g., 60 seconds).
  - `limit`: Maximum number of requests allowed within the interval.
  
- **Response**: Saved configuration in JSON format.

### 2. Check Rate Limit

**GET** `/api/is_rate_limited/{unique_token}`

- **Description**: Check if a user is rate-limited.
- **Path Parameter**:
  - `unique_token` (string): A unique identifier for the user.
  
- **Response**: `true` if the user is rate-limited, otherwise `false`.

## Project Structure

```plaintext
├── rate_limiter/
│   ├── __pycache__/
│   ├── stores/
│   ├── tests/
│   ├── main.py
│   ├── rate_limiter.py
│   ├── settings.py
│   ├── config.json
│   └── requirements.txt
```

- **`main.py`**: The main entry point for the FastAPI application.
- **`rate_limiter.py`**: Contains logic for rate limiting functionality.
- **`stores/`**: Module for storing configuration and user-specific data. Includes Redis and in-memory implementations.
- **`tests/`**: Test cases for the application.
- **`config.json`**: Stores rate limiting configurations.

## Documentation
[Here's](https://dharmapv.notion.site/Design-Document-Rate-limiting-service-cb24a3158d5d40dfa824c79421bc0e34?pvs=4) more detailed design document.
Links to specific sections:
* [Design considerations](https://dharmapv.notion.site/Design-Document-Rate-limiting-service-cb24a3158d5d40dfa824c79421bc0e34#3929186f15c34bd08092dc499544f3c6)
* [Request flow](https://dharmapv.notion.site/Design-Document-Rate-limiting-service-cb24a3158d5d40dfa824c79421bc0e34#3cd616d05fc841a99c9102f0274f362f)
* [Edge Cases](https://dharmapv.notion.site/Design-Document-Rate-limiting-service-cb24a3158d5d40dfa824c79421bc0e34#2ab92dfa753b41e8a6f71539b8f787b3)

## Testing

To run the tests:

```bash
ENV=test pytest -v
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
