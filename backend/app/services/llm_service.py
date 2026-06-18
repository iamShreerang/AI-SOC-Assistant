"""LLM service for generating incident summaries using Groq."""

import logging
from typing import Optional

from groq import Groq
from groq import APIError, RateLimitError

from app.utils.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Groq] = None


def get_client() -> Optional[Groq]:
    """Get or create Groq client."""
    global _client
    if _client is None and settings.groq_api_key:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def generate_incident_summary(incident_data: dict) -> Optional[str]:
    """
    Generate AI-powered incident summary using Groq LLM.
    
    Args:
        incident_data: Dictionary with incident details (title, description, alert_ids, status)
    
    Returns:
        Generated summary string, or None if generation fails
    """
    client = get_client()
    
    if not client:
        logger.warning("Groq API key not configured - skipping summary generation")
        return None
    
    prompt = f"""Analyze this security incident and provide a concise professional summary:

Incident Title: {incident_data['title']}
Description: {incident_data.get('description', 'No additional details provided')}
Related Alerts: {len(incident_data.get('alert_ids', []))} alerts
Current Status: {incident_data['status']}

Provide:
1. Executive Summary (2-3 sentences)
2. Key Findings and Indicators
3. Recommended Immediate Actions

Keep response under 300 words. Be specific and actionable."""

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior cybersecurity analyst with expertise in incident response and threat intelligence."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        summary = completion.choices[0].message.content
        logger.info(f"Generated summary for incident: {incident_data.get('title', 'unknown')} ({len(summary)} chars)")
        return summary
    
    except RateLimitError:
        logger.error("Groq rate limit exceeded - summary generation failed")
        return None
    
    except APIError as e:
        logger.error(f"Groq API error: {e}")
        return None
    
    except Exception as e:
        logger.error(f"Unexpected error generating summary: {e}")
        return None
