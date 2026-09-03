from app.core.llm_client import gemini_client, GEMINI_FALLBACK_MODEL

response = gemini_client.models.generate_content(
    model=GEMINI_FALLBACK_MODEL,
    contents="Return ONLY this JSON, nothing else: {\"test\": \"ok\"}",
    config={"temperature": 0},
)
print(response.text)