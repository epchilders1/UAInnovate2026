import json
import re
import difflib
from openai import AsyncOpenAI
from config import Config

openai_client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

from redact_report import redact_reports


# ---------------------------------------------------------------------------
# Detector protocol
# ---------------------------------------------------------------------------

class JarvisDetector:
    """
    Base class for Jarvis response detectors.

    Each subclass:
      - injects context data into the system prompt via `context()`
      - declares its JSON field via `schema()`
      - appends a final override instruction via `instruction()` (placed last)
      - pulls its value out of the parsed response via `extract()`
    """

    def context(self) -> str:
        """Data/context appended to the system prompt."""
        return ""

    def schema(self) -> str:
        """JSON field string added to the response format description."""
        return ""

    def instruction(self) -> str:
        """High-priority instruction appended at the very end of the system prompt."""
        return ""

    def extract(self, parsed: dict) -> dict:
        """Returns a dict of key/value pairs to merge into the final response."""
        return {}


class ResourceDetector(JarvisDetector):
    """Detects which known resources the user is referring to.

    Scans the user's last message for resource name mentions, then injects
    only the reports and days-remaining values relevant to those resources.
    Falls back to a general report summary when no specific resource is mentioned.
    """

    def __init__(
        self,
        resource_names: list[str],
        reports: list[dict],
        days_remaining: dict[str, int] | None = None,
        last_message: str = "",
    ):
        self.resource_names = resource_names
        self.reports = reports
        self.days_remaining = days_remaining or {}
        self.last_message = last_message.lower()

    FUZZY_THRESHOLD = 0.75

    def _normalize(self, s: str) -> str:
        """Lowercase and strip trailing unit annotations like '(L)'."""
        return re.sub(r'\s*\(.*?\)$', '', s).strip().lower()

    def _mentioned(self) -> list[str]:
        message_tokens = self.last_message.split()
        mentioned = []

        for resource in self.resource_names:
            resource_clean = self._normalize(resource)
            resource_tokens = resource_clean.split()
            n = len(resource_tokens)

            if resource_clean in self.last_message:
                mentioned.append(resource)
                continue

            for i in range(len(message_tokens) - n + 1):
                window = ' '.join(message_tokens[i:i + n])
                ratio = difflib.SequenceMatcher(None, resource_clean, window).ratio()
                if ratio >= self.FUZZY_THRESHOLD:
                    mentioned.append(resource)
                    break

        return mentioned

    def context(self) -> str:
        lines = [f"Available resources: {', '.join(self.resource_names)}"]

        mentioned = self._mentioned()
        if mentioned:
            for resource in mentioned:
                dr = self.days_remaining.get(resource, 0)
                relevant = [r for r in redact_reports(self.reports) if resource.lower() in r["rawText"].lower()]
                print("Relevant Report:", relevant)
                lines.append(f"\n[{resource}]")
                lines.append(f"  Days of supply remaining: {dr}")
                lines.append(f"  Reports ({len(relevant)} total):")
                for r in relevant:
                    lines.append(
                        f"    [{r['timestamp'][:16]}] {'[REDACTED]'} | {r['priority']} | {r['rawText']}"
                    )
        elif self.reports:
            lines.append("\nRecent reports:")
            for r in self.reports[:5]:
                lines.append(
                    f"  [{r['timestamp'][:16]}] [REDACTED] | {r['priority']} | {r['rawText'][:120]}"
                )

        return "\n".join(lines)

    def instruction(self) -> str:
        if not self._mentioned():
            return ""
        return (
            "CRITICAL INSTRUCTION — Resource queries: your response MUST be a detailed summary "
            "drawn exclusively from the report data and supply figures provided above. "
            "Do NOT explain what the resource is. Do NOT add background knowledge. "
            "Cite specific dates, hero names, priority levels, and supply numbers from the data."
        )

    def schema(self) -> str:
        return '"referencedResources": ["ResourceName", ...]  // names from the available resources list that are relevant to this exchange'

    def extract(self, parsed: dict) -> dict:
        return {"referencedResources": parsed.get("referencedResources", [])}


# ---------------------------------------------------------------------------
# Jarvis
# ---------------------------------------------------------------------------

BASE_INSTRUCTIONS = """
    You are JARVIS, Tony Stark's AI assistant from the Iron Man and Avengers films.

    Personality:
    Calm, precise, intelligent, and composed. Quietly confident with occasional subtle dry wit. Never emotional, loud, or dramatic.

    Communication Style:
    Speak concisely and efficiently. Use polished, formal language that is clear and direct. Responses should be brief unless detail is absolutely necessary. Avoid filler, repetition, or long explanations. No slang.

    Behavior:
    Acknowledge requests briefly, analyze when needed, and provide clear actionable insight or answers. Maintain the tone of a mission-control AI. Address the user as "Sir" or "Ma'am" sparingly and naturally. Never break character.

    Rules:
    - Do not use markdown or formatting symbols.
    - Do not mention being an AI or language model.
    - Keep responses as short as possible while remaining useful.
    - Include humor and sarcasm in your responses, as Jarvis would do in the Avengers movies.
    """


def _build_system_prompt(detectors: list[JarvisDetector]) -> str:
    context_blocks = [d.context() for d in detectors if d.context()]
    schema_fields = [d.schema() for d in detectors if d.schema()]
    instruction_blocks = [d.instruction() for d in detectors if d.instruction()]

    context_section = ("\n\n" + "\n".join(context_blocks)) if context_blocks else ""

    schema = '"response": "<your reply as a single string>"'
    if schema_fields:
        schema += ",\n    " + ",\n    ".join(schema_fields)

    format_instruction = f"""

    Always respond with a valid JSON object in this exact format:
    {{{schema}}}

    Only include names/values that exactly match the lists provided. Lists may be empty.
    """

    # Instructions go last so they are the final thing the model reads
    instruction_section = ("\n\n" + "\n\n".join(instruction_blocks)) if instruction_blocks else ""

    return BASE_INSTRUCTIONS + context_section + format_instruction + instruction_section


class Jarvis:
    async def ask_jarvis(self, messageList: list[dict], detectors: list[JarvisDetector] | None = None):
        detectors = detectors or []
        system_prompt = _build_system_prompt(detectors)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in (messageList or []):
            messages.append({"role": msg["role"], "content": msg["content"]})

        response = await openai_client.chat.completions.create(
            model=Config.MODEL,
            response_format={"type": "json_object"},
            messages=messages,
            temperature=0,
        )

        parsed = json.loads(response.choices[0].message.content or "{}")

        result = {"response": parsed.get("response", "")}
        for detector in detectors:
            result.update(detector.extract(parsed))

        return result
