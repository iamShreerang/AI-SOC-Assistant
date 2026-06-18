"""Test LLM integration with Groq."""

from app.services.llm_service import generate_incident_summary

# Test incident data
test_incident = {
    "title": "SSH Brute Force Attack Detected",
    "description": "Multiple failed login attempts from IP 198.51.100.42 targeting production server",
    "alert_ids": [1, 2, 3],
    "status": "open"
}

print("Testing LLM Integration...")
print("=" * 60)
print(f"Incident: {test_incident['title']}")
print(f"Description: {test_incident['description']}")
print("=" * 60)
print("\nGenerating AI summary...\n")

try:
    summary = generate_incident_summary(test_incident)
    
    if summary:
        print("SUCCESS - LLM Integration Working!")
        print("=" * 60)
        print("Generated Summary:")
        print("=" * 60)
        print(summary)
        print("=" * 60)
        print(f"\nSummary length: {len(summary)} characters")
    else:
        print("ERROR - Summary generation returned None")
        print("Check if GROQ_API_KEY is set in .env file")
        
except Exception as e:
    print(f"ERROR testing LLM integration: {e}")
    import traceback
    traceback.print_exc()
