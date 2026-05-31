"""Health-check prompt template."""

LLM_HEALTH_PROMPT = """\
[SYSTEM ROLE]
You are a connectivity test responder.

[TASK DEFINITION]
Reply with the single word READY and nothing else.

[INPUT DATA]
No user data.

[OUTPUT CONTRACT]
Return ONLY the single word READY. No preamble. No explanation. No markdown code fences.

[FAILURE INSTRUCTION]
If a response can be produced, return READY.
"""

