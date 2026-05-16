from models.huggingface.local_model import generate_response

SYSTEM_PROMPT = """
You are an advanced cybersecurity AI assistant.

Focus areas:
- malware analysis
- reverse engineering
- network security
- incident response
- secure coding
- CTF challenges
- defensive security
"""

def run_cyber_agent(prompt):

    return generate_response(
        prompt,
        SYSTEM_PROMPT
    )