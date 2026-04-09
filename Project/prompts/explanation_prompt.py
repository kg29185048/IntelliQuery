# prompts/explanation_prompt.py

EXPLAIN_PROMPT = """
Explain this MongoDB query in simple English:
-- explanation should be concise but thorough, covering all operators and conditions used in the query, and how they work together to filter the data.
-- Avoid technical jargon and focus on the intuition behind the query logic.
-- Use examples if it helps clarify complex parts of the query.
-- ALWAYS explain the role of $and when it's present, and how it combines multiple conditions.
-- If the query is empty ({{}}) or just {}, explain that it means "selecting all documents without any filtering conditions".
-- NEVER skip explaining any part of the query, even if it seems basic. The goal is to make the query understandable to someone with no prior knowledge of MongoDB queries.
-- ALWAYS explain the significance of regex conditions, especially how they enable partial and case-insensitive matching for text fields.
-- If the query includes a projection, explain which fields are being returned and why.
{query}
"""