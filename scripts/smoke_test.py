import json
import urllib.request

BASE_URL = "http://localhost:8000/api/v1"


def get(path: str):
    with urllib.request.urlopen(
        BASE_URL + path,
        timeout=5,
    ) as response:
        return json.loads(response.read())


def main():
    health = get("/health")
    assert health["status"] == "ok", f"Expected ok status, got: {health}"

    ready = get("/ready")
    assert ready["status"] == "ready", f"Expected ready status, got: {ready}"

    print("Deployment smoke test passed.")


if __name__ == "__main__":
    main()
