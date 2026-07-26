import requests
import certifi
import os
import random


used_images = set()


def get_image_url(query):

    url = "https://api.unsplash.com/search/photos"

    headers = {
        "Authorization": f"Client-ID {os.getenv('UNSPLASH_ACCESS_KEY')}"
    }

    params = {
        "query": query,
        "per_page": 30,
        "orientation": "landscape",
        "content_filter": "high"
    }

    try:

        res = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10,
            verify=certifi.where()
        )
        if res.status_code != 200:
            return None

        data = res.json()

        available = [
            img for img in data["results"]
            if img["id"] not in used_images
        ]

        # If all are used, reset for this query
        if not available:
            available = data["results"]

        selected = random.choice(available)

        used_images.add(selected["id"])

        return selected["urls"]["small"]

    except Exception as e:

        print("Image error:", e)

        return None
