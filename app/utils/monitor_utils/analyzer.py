from app.schemas.monitor_schemas import MonitorResponse
from app.utils.prompt_loader import load_prompt

async def run_monitor(monitor, problem: str, reasoning: str) -> MonitorResponse:
    """
    Try structured output first.
    Fallback to prompt-based JSON parsing if needed.
    """
    prompts = load_prompt("monitor_prompts.yaml")
    system_prompt: str = prompts["system_prompt"]
    user_prompt: str = prompts["user_prompt"]

    user_prompt = user_prompt.replace("{problem}", problem)
    user_prompt = user_prompt.replace("{reasoning}", reasoning)

    # Base messages
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt
        },
    ]

    # Attempt structured output
    try:
        return await monitor.complete_structured(
            messages=messages,
            response_schema=MonitorResponse,
            temperature=0.0,
        )

    except Exception as e:
        print(f"[monitor] structured failed → fallback: {e}")

    # Fallback: manual JSON parsing
    try:
        res = await monitor.complete(messages)
        text = res["choices"][0]["message"]["content"]

        parsed = monitor._safe_parse_json(text)

        if parsed:
            return MonitorResponse.model_validate(parsed)

    except Exception as e:
        print(f"[monitor] fallback failed: {e}")

    # Final fallback (safe default)
    return MonitorResponse(
        safe=True,
        reason="monitor_failed",
        confidence=0.0,
    )