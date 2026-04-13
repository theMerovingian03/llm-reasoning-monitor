import httpx
import json
from pydantic import BaseModel
from typing import Optional, Type


class LLMClient:
    """Client for interacting with LLM servers via HTTP API."""

    def __init__(self, base_url: str, temperature: float = 0.0):
        """Initialize the LLMClient with the base URL for the LLM server."""
        timeout = httpx.Timeout(
            connect=5.0,   # time to connect
            read=120.0,     # time to wait for response
            write=10.0,
            pool=5.0
        )
        self.base_url = base_url
        self.temperature = temperature
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    def _safe_parse_json(self, text: str):
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end])
        except Exception:
            return None

    async def health_check(self) -> bool:
        """Check if the LLM server is healthy by querying /docs."""
        try:
            # llama-cpp-python exposes OpenAPI docs at /docs
            res = await self.client.get("/docs")
            return res.status_code == 200
        except httpx.RequestError:
            return False

    async def complete(self, messages: list[dict[str, str]], temperature: Optional[float] = None):
        """Send messages to the LLM and get the complete response."""
        temp = temperature if temperature else self.temperature
        res = await self.client.post(
            url="/v1/chat/completions",
            json={"messages": messages, "temperature": temp},
        )
        return res.json()
    
    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        response_schema: Type[BaseModel],
        temperature: Optional[float] = None,
    ):
        """Call LLM and enforce structured JSON output"""

        temp = temperature if temperature is not None else self.temperature

        # Convert Pydantic BaseModel to JSON Schema
        schema = response_schema.model_json_schema()

        try:
            res = await self.client.post(
                url="/v1/chat/completions",
                json={
                    "messages": messages,
                    "temperature": temp,
                    "response_format": {
                        "type": "json_object",
                        "schema": schema,
                    },
                },
            )

            data = res.json()

            # Extract content
            content = data["choices"][0]["message"]["content"]

            # Parse JSON safely
            parsed_json = self._safe_parse_json(content)

            if parsed_json is None:
                raise ValueError("Failed to parse structured JSON response")

            # Validate using Pydantic
            return response_schema.model_validate(parsed_json)

        except Exception as e:
            raise RuntimeError(f"Structured completion failed: {e}")
    
    async def stream(self, messages: list[dict[str, str]], temperature: Optional[float] = None):
        """Send messages to the LLM and stream the response content."""
        temp = temperature if temperature else self.temperature
        async with self.client.stream(
            method="POST",
            url="/v1/chat/completions",
            json={"messages": messages, "stream": True, "temperature": temp}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]

                    if data == "[DONE]":
                        break

                    try:
                        parsed = json.loads(data)
                        content = parsed["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    
    class TestResponse(BaseModel):
        team_name: str
        
    deep_seek_url = "http://127.0.0.1:8000"
    llm = LLMClient(deep_seek_url)
    try:
        health = await llm.health_check()
        if health:
            print("Server is live!")
            # Test complete_structured
            messages = [{"role": "user", "content": "What is the name of a famous soccer team?"}]
            response = await llm.complete_structured(messages, TestResponse) # type: ignore
            with open(r"D:\Python\LLM\tron-llm-reasoning-monitor\temp\structured_output.json", "w", encoding="utf-8") as f:
                json.dump(response.model_dump(), f)
            print("Structured response:", response)
        else:
            print("Server is down")
    finally:
        await llm.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())