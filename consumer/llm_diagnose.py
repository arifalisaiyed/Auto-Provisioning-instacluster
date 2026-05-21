import logging
import os
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

VALID_ACTIONS = {"restart_server", "clear_temp_files", "run_hello_world_script", "scale_up_resources"}

_SYSTEM = (
    "You are an expert infrastructure reliability engineer. "
    "Given server health metrics and triggered threshold violations, diagnose the issue "
    "and recommend exactly one remediation action.\n\n"
    "Always respond in exactly this format (two parts, nothing else):\n"
    "<diagnosis: one concise paragraph explaining the issue>\n"
    "ACTION: <one of: restart_server | clear_temp_files | run_hello_world_script | scale_up_resources>"
)

_HUMAN = (
    "Server: {server_id}\n"
    "CPU: {cpu_percent}%\n"
    "Memory: {memory_percent}%\n"
    "Disk: {disk_percent}%\n"
    "Network In: {bytes_in} bytes\n"
    "Network Out: {bytes_out} bytes\n"
    "Triggered thresholds: {triggered}\n\n"
    "Diagnose the issue and recommend the appropriate action."
)

_prompt = ChatPromptTemplate.from_messages([("system", _SYSTEM), ("human", _HUMAN)])


def _build_chain():
    llm = ChatGroq(
        api_key=os.environ["GROQ_API_KEY"],
        model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
        temperature=0.1,
    )
    return _prompt | llm | StrOutputParser()


_chain = None


def diagnose(stats: dict, triggered: list[str]) -> tuple[str, str]:
    global _chain
    if _chain is None:
        _chain = _build_chain()

    response = _chain.invoke({
        "server_id":       stats["server_id"],
        "cpu_percent":     stats["cpu_percent"],
        "memory_percent":  stats["memory_percent"],
        "disk_percent":    stats["disk_percent"],
        "bytes_in":        stats["bytes_in"],
        "bytes_out":       stats["bytes_out"],
        "triggered":       ", ".join(triggered),
    })

    # Parse: last line starting with "ACTION:" is the action keyword
    lines = [l.strip() for l in response.strip().splitlines() if l.strip()]
    action = "run_hello_world_script"  # safe default
    diagnosis_lines = lines

    for i, line in enumerate(lines):
        match = re.match(r"^ACTION:\s*(\w+)$", line, re.IGNORECASE)
        if match:
            candidate = match.group(1).lower()
            if candidate in VALID_ACTIONS:
                action = candidate
            diagnosis_lines = lines[:i]
            break

    diagnosis = " ".join(diagnosis_lines)
    logger.info("LLM diagnosed '%s' for %s → action: %s", triggered, stats["server_id"], action)
    return diagnosis, action
