import requests
import time

BASE_URL = "http://127.0.0.1:8000"
VERSION_ID = "55ccdbe8-8d24-4dec-bcd2-6164703a3180"

URL = f"{BASE_URL}/assets/public/{VERSION_ID}"

TOTAL_REQUESTS = 50

success = 0
start = time.time()

# 🔥 Use persistent session (important!)
with requests.Session() as session:
    for i in range(TOTAL_REQUESTS):
        response = session.head(URL)
        if response.status_code == 200:
            success += 1

end = time.time()

total_time = end - start
avg_latency = total_time / TOTAL_REQUESTS

print("------ Benchmark Results ------")
print("Total Requests:", TOTAL_REQUESTS)
print("Successful:", success)
print("Total Time:", round(total_time, 2), "seconds")
print("Average Latency:", round(avg_latency, 4), "seconds")
