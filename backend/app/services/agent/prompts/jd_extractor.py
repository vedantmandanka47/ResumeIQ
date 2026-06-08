"""JD extraction prompt template for URL-based job description analysis."""

JD_EXTRACT_PROMPT = """
Use Google Search to fetch the job posting at this URL: {job_url}

Extract and return ONLY a JSON object with:
{{
  "extracted_text": "<full concatenated job description text>",
  "required_skills": ["<skill>"],
  "preferred_skills": ["<skill>"],
  "experience_years": <int or null>,
  "role_title": "<string>",
  "company_name": "<string>"
}}

Do not include any other text.
"""
