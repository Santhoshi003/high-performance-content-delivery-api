#  High Performance Content Delivery API with Edge Caching

A production-grade Content Delivery API built with **FastAPI**, designed for high performance, scalability, and modern HTTP caching standards.

This system leverages:

* Strong ETag-based caching
* Immutable asset versioning
* Secure temporary access tokens
* PostgreSQL for metadata
* S3-compatible object storage (MinIO)
* Docker-based environment
* Automated testing & benchmarking

---

# 🚀 Features

## ✅ Core Capabilities

* Upload assets to object storage
* Serve mutable and immutable assets
* Strong SHA256 ETag generation
* Conditional GET support (`If-None-Match`)
* 304 Not Modified responses
* Versioned immutable assets
* Secure short-lived access tokens
* HTTP caching optimized for CDN usage

---

# 🏗 Architecture Overview

```
Client
   ↓
CDN (Cloudflare / CloudFront)
   ↓
FastAPI Origin Server
   ↓
PostgreSQL (Metadata)
   ↓
MinIO / S3 (Object Storage)
```

### Request Flow (Immutable Asset)

1. Client requests `/assets/public/{version_id}`
2. CDN checks edge cache
3. If cached → served directly from edge
4. If not cached → CDN fetches from origin
5. Origin retrieves object from storage
6. Response cached for 1 year

---

# 🧰 Tech Stack

* Python 3.12
* FastAPI
* PostgreSQL
* MinIO (S3-compatible storage)
* SQLAlchemy
* Docker & Docker Compose
* Pytest
* HTTPX (testing & benchmarking)

---

# 📁 Project Structure

```
content-delivery-api/
│
├── app/                    # Core application modules
├── tests/                  # Automated test suite
├── scripts/                # Benchmark script
├── main.py                 # FastAPI entrypoint
├── docker-compose.yml
├── requirements.txt
├── submission.yml
├── README.md
├── ARCHITECTURE.md
├── PERFORMANCE.md
└── .env.example
```

---

# ⚙️ Setup Instructions (Local Development)

## 1️⃣ Clone Repository

```bash
git clone https://github.com/Santhoshi003/high-performance-content-delivery-api.git
cd high-performance-content-delivery-api
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Start Infrastructure (Docker)

```bash
docker-compose build
docker-compose up -d
```

This starts:

* PostgreSQL
* MinIO (S3-compatible object storage)

---

## 5️⃣ Run API

```bash
uvicorn main:app --reload
```

API available at:

```
http://127.0.0.1:8000
```

Swagger documentation:

```
http://127.0.0.1:8000/docs
```

---

# 🔐 Environment Variables

Create a `.env` file using `.env.example` as reference:

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/assets
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=assets
```

---

# 📡 API Endpoints

## Upload Asset

```
POST /assets/upload
```

Returns:

* id
* etag
* size

---

## Download Mutable Asset

```
GET /assets/{id}/download
```

Supports:

* If-None-Match header
* Returns 304 if unchanged

Cache-Control:

```
public, s-maxage=3600, max-age=60
```

---

## HEAD Request

```
HEAD /assets/{id}/download
```

Returns headers only (no body).

---

## Publish Immutable Version

```
POST /assets/{id}/publish
```

Creates new immutable version.

---

## Get Immutable Version

```
GET /assets/public/{version_id}
```

Cache-Control:

```
public, max-age=31536000, immutable
```

---

## Generate Access Token

```
POST /assets/{id}/generate-token
```

Returns secure temporary token.

---

## Access Private Asset

```
GET /assets/private/{token}
```

Cache-Control:

```
private, no-store, no-cache, must-revalidate
```

---

# 🧪 Run Tests

```bash
pytest
```

Expected output:

```
3 passed
```

---

# 📊 Run Benchmark

```bash
python scripts/run_benchmark.py
```

Example output:

```
Total Requests: 50
Successful: 50
Average Latency: 0.01 seconds
```

---

# 🚀 Performance & Caching Strategy

## Immutable Assets

* Versioned URLs
* Cached for 1 year
* No invalidation required
* CDN hit ratio >95%

## Mutable Assets

* Short browser cache
* Longer CDN cache (s-maxage)
* Conditional requests supported

## Private Assets

* Never cached
* Secure expiring tokens

---

# 🔒 Security Considerations

* SHA256 strong ETags
* Cryptographically secure token generation
* Token expiration enforcement
* Proper HTTP status codes
* No sensitive credentials stored in repository

---

# 🧠 Design Decisions

* Storage decoupled from API
* ETags stored in DB (no recalculation per request)
* Immutable versioning avoids cache invalidation complexity
* Benchmarked using persistent HTTP sessions

---

# 📄 Submission Support Files

* ARCHITECTURE.md → system design & flow
* PERFORMANCE.md → benchmark results
* submission.yml → automated evaluation commands

---

# 🏁 Conclusion

This project demonstrates:

* Advanced HTTP caching strategies
* CDN-optimized API design
* Secure content delivery
* Production-ready architecture
* Automated testing and benchmarking

---
