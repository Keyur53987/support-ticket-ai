import json
import google.generativeai as genai
from .retrieval import retrieve_and_rerank

def generate_decision(ticket_message: str) -> dict:
    # Retrieve context
    retrieved_context = retrieve_and_rerank(ticket_message)
    
    if not retrieved_context:
        # Cannot make a decision without context
        return {
            "action": "NEEDS_MORE_INFORMATION",
            "confidence": 0.0,
            "reason": "No relevant policy documents found to evaluate the ticket.",
            "sources": []
        }
        
    context_text = "\n\n".join([f"Source: {ctx['source']}\n{ctx['text']}" for ctx in retrieved_context])
    sources = list(set([ctx['source'] for ctx in retrieved_context]))
    
    prompt = f"""You are an AI Support Ticket Decision Assistant.
Evaluate the following customer support ticket against the provided policy context.

Policy Context:
{context_text}

Ticket:
{ticket_message}

You must return a structured JSON object with the following fields:
- "action": A short string representing the action to take (e.g., "REQUEST_PHOTOS", "APPROVE_REFUND", "DENY_RETURN", "NEEDS_MORE_INFORMATION")
- "confidence": A float between 0.0 and 1.0 indicating how confident you are in this decision based on the policy.
- "reason": A brief explanation of why this action was chosen based on the policy.
- "sources": A list of source filenames used to make this decision (from the provided context).

If the ticket is missing explicitly required fields that prevent a final decision, you can return "NEEDS_MORE_INFORMATION", but try your best to infer the situation from the user's message first.

Respond ONLY with the raw JSON object. Do not include markdown code blocks.
"""
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    
    try:
        raw_text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
        decision_data = json.loads(raw_text)
        
        # Ensure sources is a list of strings
        if not isinstance(decision_data.get("sources"), list):
            decision_data["sources"] = sources
            
        return decision_data
    except Exception as e:
        print(f"Error parsing LLM response: {e}\nResponse: {response.text}")
        return {
            "action": "ERROR",
            "confidence": 0.0,
            "reason": "Failed to parse AI decision.",
            "sources": sources
        }
