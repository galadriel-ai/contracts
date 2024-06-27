import httpx

TIMEOUT = httpx.Timeout(timeout=600.0, connect=10.0)
