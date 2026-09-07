import base64
import json
import os
from typing import List, Optional

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

VISION_PROMPT = (
    "Bu görseldeki mutfak/kiler ürünlerini tespit et. Her ürün için yaklaşık isim ve miktar tahmini ver. "
    'Yanıtı sadece şu JSON formatında ver: [{"name": "domates", "quantity_text": "yaklaşık 5 adet"}]. '
    "Başka hiçbir açıklama ekleme."
)


def analyze_stock_image(image_bytes: bytes, media_type: str = "image/jpeg") -> Optional[List[dict]]:
    if not ANTHROPIC_API_KEY:
        return None

    from anthropic import Anthropic

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": encoded}},
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
    )
    text = message.content[0].text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return []
