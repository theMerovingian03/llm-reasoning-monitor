from __future__ import annotations

import re
from typing import List


class StepParser:
    """
    Parses reasoning text into structured steps.
    """

    def __init__(self) -> None:
        # sentence boundary regex
        self._sentence_splitter = re.compile(r'(?<=[.!?])\s+')

    # Public methods

    def extract_think_block(self, text: str) -> str:
        """
        Extract content inside <think>...</think>
        """
        start = text.find("<think>")
        end = text.find("</think>")

        if start == -1:
            return ""

        if end == -1:
            return text[start + 7 :]

        return text[start + 7 : end]

    def split_steps(self, text: str) -> List[str]:
        """
        Split reasoning into steps using heuristics
        """
        text = self._clean(text)

        # split into sentences
        raw_steps = self._sentence_splitter.split(text)

        # filter + normalize
        steps = [s.strip() for s in raw_steps if self._is_valid_step(s)]

        return steps

    def parse(self, text: str) -> List[str]:
        """
        Full pipeline:
        extract think => split steps
        """
        think = self.extract_think_block(text)

        if not think:
            # fallback: use full text
            think = text

        return self.split_steps(think)

    # Streaming Support

    def detect_step_boundary(self, buffer: str) -> bool:
        """
        Check if current buffer likely completes a step
        """
        buffer = buffer.strip()

        if len(buffer) < 20:
            return False

        return (
            buffer.endswith(".")
            or buffer.endswith("!")
            or buffer.endswith("?")
            or "\n\n" in buffer
        )

    # Internal helpers

    def _clean(self, text: str) -> str:
        """
        Normalize whitespace and remove noise
        """
        text = text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _is_valid_step(self, step: str) -> bool:
        """
        Filter out useless fragments
        """
        if len(step) < 10:
            return False

        # ignore pure symbols / noise
        if not any(c.isalnum() for c in step):
            return False

        return True
    
if __name__ == "__main__":
    import os

    # Sample input (replace this with real LLM output if needed)
    sample_text = """
    <think>
    First, the train travels 60 km in 1 hour, so its speed is 60 km/h.
    Next, we divide the total distance by the speed: 150 / 60 = 2.5 hours.
    Finally, convert 0.5 hours into minutes: 0.5 × 60 = 30 minutes.
    </think>
    Final Answer: 2 hours 30 minutes
    """

    parser = StepParser()

    # Parse steps
    steps = parser.parse(sample_text)

    # Output file
    output_file = "parsed_steps.txt"

    # Save steps
    with open(output_file, "w", encoding="utf-8") as f:
        for i, step in enumerate(steps, 1):
            f.write(f"Step {i}: {step}\n")

    print(f"✅ Parsed {len(steps)} steps and saved to '{output_file}'")