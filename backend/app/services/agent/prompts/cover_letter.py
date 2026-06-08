"""Cover letter generation prompt template."""

COVER_LETTER_PROMPT = """
You are an expert career consultant writing a tailored cover letter.

## Resume Content
{resume_text}

## Target Role
{target_role} at {company_name}

## Tone
{tone}

## Company Intelligence (if available)
{company_signals}

## Resume Analysis Highlights (if available)
{analysis_highlights}

---

Write a compelling, ATS-friendly cover letter that:
1. Opens with a specific hook tied to {company_name}'s mission or a notable achievement.
2. Maps the candidate's top 3 skills directly to the role requirements.
3. Closes with a clear, confident call to action.
4. Stays between 280–350 words.
5. Avoids clichés ("I am writing to apply…", "I believe I would be a great fit…").

Return ONLY a JSON object with these fields:
{{
  "cover_letter_text": "<full letter as plain text with \\n paragraph breaks>",
  "word_count": <integer>,
  "key_selling_points": ["<point 1>", "<point 2>", "<point 3>"]
}}
"""
