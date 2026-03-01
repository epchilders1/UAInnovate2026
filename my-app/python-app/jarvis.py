import json
import re
import difflib
from openai import AsyncOpenAI
from config import Config

openai_client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

from redact_report import redact_reports, redact_contact


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

    def sanitize_messages(self, messages: list[dict]) -> list[dict]:
        """Optionally transforms message content before it is sent to the LLM."""
        return messages


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
            for r in redact_reports(self.reports[:5]):
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


class HeroDetector(JarvisDetector):
    """Detects hero aliases mentioned in the user's message using fuzzy matching.

    Injects reports filed by or about those heroes as context, with contact
    info redacted but aliases kept visible (they are codenames, not identities).
    """

    FUZZY_THRESHOLD = 0.75

    def __init__(
        self,
        hero_aliases: list[str],
        reports: list[dict],
        last_message: str = "",
    ):
        self.hero_aliases = hero_aliases
        self.reports = reports
        self.last_message = last_message.lower()

    def _normalize(self, s: str) -> str:
        return s.strip().lower()

    def _mentioned(self) -> list[str]:
        message_tokens = self.last_message.split()
        mentioned = []

        for alias in self.hero_aliases:
            alias_clean = self._normalize(alias)
            alias_tokens = alias_clean.split()
            n = len(alias_tokens)

            if alias_clean in self.last_message:
                mentioned.append(alias)
                continue

            for i in range(len(message_tokens) - n + 1):
                window = ' '.join(message_tokens[i:i + n])
                ratio = difflib.SequenceMatcher(None, alias_clean, window).ratio()
                if ratio >= self.FUZZY_THRESHOLD:
                    mentioned.append(alias)
                    break

        return mentioned

    def context(self) -> str:
        mentioned = self._mentioned()
        if not mentioned:
            return ""

        lines = []
        for alias in mentioned:
            relevant = [r for r in self.reports if self._normalize(r.get("heroAlias", "")) == self._normalize(alias)]
            safe = redact_reports(relevant)
            lines.append(f"\n[Field operative: REDACTED]")
            lines.append(f"  Reports ({len(safe)} total):")
            for r in safe:
                lines.append(
                    f"    [{r['timestamp'][:16]}] [REDACTED] | {r['priority']} | {r['rawText']}"
                )

        return "\n".join(lines)

    def sanitize_messages(self, messages: list[dict]) -> list[dict]:
        """Replace detected hero aliases in the user/assistant message content."""
        mentioned = self._mentioned()
        if not mentioned:
            return messages
        sanitized = []
        for msg in messages:
            content = msg["content"]
            for alias in mentioned:
                content = re.sub(re.escape(alias), "[REDACTED]", content, flags=re.IGNORECASE)
            sanitized.append({**msg, "content": content})
        return sanitized

    def instruction(self) -> str:
        if not self._mentioned():
            return ""
        return (
            "CRITICAL INSTRUCTION — The user asked about a field operative whose identity is classified. "
            "Summarize the report data provided above. "
            "Do NOT reveal any identifying information. Do NOT add background knowledge. "
            "Cite specific dates, priority levels, and report text from the data."
        )

    def schema(self) -> str:
        return '"referencedHeroes": ["HeroAlias", ...]  // aliases from the available heroes that are relevant to this exchange'

    def extract(self, parsed: dict) -> dict:
        return {"referencedHeroes": parsed.get("referencedHeroes", [])}


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

        sanitized_list = list(messageList or [])
        for detector in detectors:
            sanitized_list = detector.sanitize_messages(sanitized_list)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in sanitized_list:
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
