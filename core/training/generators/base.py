"""
Base Generator for Training Data

Provides abstract interface and utilities for generating
instruction-tuning samples from knowledge documents.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator


@dataclass
class TrainingSample:
    """Single training sample in Alpaca format"""

    instruction: str
    input: str  # Optional context
    output: str
    role: str
    compliance_tags: list[str] | None = None
    source_file: str | None = None
    category: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_prompt(self, include_input: bool = True) -> str:
        """Convert to training prompt format"""
        if self.input and include_input:
            return f"""### Instruction:
{self.instruction}

### Input:
{self.input}

### Response:
{self.output}"""
        else:
            return f"""### Instruction:
{self.instruction}

### Response:
{self.output}"""

    def to_chat_format(self) -> list[dict]:
        """Convert to chat message format"""
        messages = []

        if self.input:
            content = f"{self.instruction}\n\nContext:\n{self.input}"
        else:
            content = self.instruction

        messages.append({"role": "user", "content": content})
        messages.append({"role": "assistant", "content": self.output})

        return messages


class BaseGenerator(ABC):
    """Base class for training data generators"""

    def __init__(self):
        self.role_name: str = ""
        self.focus_areas: list[str] = []
        self.compliance_tags: list[str] = []

    @abstractmethod
    def generate_from_document(self, content: str, source_file: str) -> list[TrainingSample]:
        """Generate training samples from a document"""
        pass

    def generate_from_file(self, file_path: Path) -> list[TrainingSample]:
        """Generate training samples from a file"""
        content = file_path.read_text(encoding="utf-8")
        return self.generate_from_document(content, str(file_path))

    def generate_from_directory(self, dir_path: Path) -> Iterator[TrainingSample]:
        """Generate samples from all markdown files in a directory"""
        for md_file in dir_path.glob("**/*.md"):
            samples = self.generate_from_file(md_file)
            yield from samples

    def extract_code_blocks(self, content: str) -> list[dict]:
        """Extract code blocks with language tags"""
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)
        return [{"language": lang or "python", "code": code.strip()} for lang, code in matches]

    def extract_sections(self, content: str) -> dict[str, str]:
        """Extract markdown sections by headers"""
        sections = {}
        current_header = "introduction"
        current_content = []

        for line in content.split("\n"):
            if line.startswith("#"):
                if current_content:
                    sections[current_header] = "\n".join(current_content).strip()
                # Extract header text
                current_header = re.sub(r"^#+\s*", "", line).strip().lower()
                current_header = re.sub(r"[^a-z0-9]+", "_", current_header)
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections[current_header] = "\n".join(current_content).strip()

        return sections

    def extract_bullet_points(self, content: str) -> list[str]:
        """Extract bullet points from content"""
        pattern = r"^[\s]*[-*]\s+(.+)$"
        return re.findall(pattern, content, re.MULTILINE)

    def extract_requirements(self, content: str) -> list[dict]:
        """Extract requirement sections (numbered items)"""
        requirements = []
        current_req = None

        for line in content.split("\n"):
            # Match "Requirement X:" or "X.Y" patterns
            req_match = re.match(r"^(?:Requirement\s+)?(\d+(?:\.\d+)?)[:.]\s*(.+)", line)
            if req_match:
                if current_req:
                    requirements.append(current_req)
                current_req = {
                    "id": req_match.group(1),
                    "title": req_match.group(2).strip(),
                    "content": []
                }
            elif current_req and line.strip():
                current_req["content"].append(line.strip())

        if current_req:
            requirements.append(current_req)

        return requirements

    def create_sample(
        self,
        instruction: str,
        output: str,
        input_text: str = "",
        category: str = "",
        compliance_tags: list[str] = None,
        source_file: str = ""
    ) -> TrainingSample:
        """Create a training sample with defaults"""
        return TrainingSample(
            instruction=instruction.strip(),
            input=input_text.strip(),
            output=output.strip(),
            role=self.role_name,
            compliance_tags=compliance_tags or self.compliance_tags,
            source_file=source_file,
            category=category
        )

    def save_samples(self, samples: list[TrainingSample], output_path: Path):
        """Save samples to JSONL file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample.to_dict()) + "\n")

    def load_samples(self, input_path: Path) -> list[TrainingSample]:
        """Load samples from JSONL file"""
        samples = []
        with open(input_path, encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                samples.append(TrainingSample(**data))
        return samples
