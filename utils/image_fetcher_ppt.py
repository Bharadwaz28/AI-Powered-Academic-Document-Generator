import requests
import os
import random
import certifi

used_images = set()


def get_guaranteed_image(query, topic, orientation=None):

    image_url = get_image_url(
        query,
        orientation=orientation
    )

    if image_url:
        return image_url

    image_url = get_image_url(query)

    if image_url:
        return image_url

    image_url = get_image_url(topic)

    if image_url:
        return image_url

    return None


def get_image_url(query, orientation=None):
    url = "https://api.unsplash.com/search/photos"

    headers = {
        "Authorization": f"Client-ID {os.getenv('UNSPLASH_ACCESS_KEY')}"
    }

    params = {
        "query": query,
        "per_page": 30,
        "order_by": "relevant",
        "content_filter": "high"
    }

    if orientation:
        params["orientation"] = orientation

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

        if not data.get("results"):
            return None

        available = [
            img for img in data["results"]
            if img["id"] not in used_images
        ]

        if not available:
            return None

        selected = random.choice(available)

        used_images.add(selected["id"])

        return selected["urls"]["regular"]

    except Exception as e:
        print("Image fetch error:", e)
        return None
