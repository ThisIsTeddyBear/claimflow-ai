from __future__ import annotations

import json
from pathlib import Path


class PromptRegistry:
    def __init__(self, prompts_dir: str) -> None:
        self.prompts_dir = Path(prompts_dir)

    def load(self, prompt_name: str, version: str = "v1") -> dict:
        prompt_path = self.prompts_dir / prompt_name / f"{version}.json"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        return json.loads(prompt_path.read_text(encoding="utf-8"))