import json
import google.generativeai as genai
from app.core.config import settings

class ReasoningEngine:
    def synthesize_report(self, repo_data: dict, bus_factor_data: dict, decay_data: dict, nlp_data: dict, releases_data: list, language: str = "English") -> dict:
        """
        Synthesizes the individual metrics to generate a conclusion using Gemini API.
        Returns the parsed JSON response.
        """
        # Set API Key directly here (FastAPI will grab it from .env or docker run)
        if not settings.GEMINI_API_KEY:
            # Fallback to local heuristic if no key is provided
            status = "AT RISK"
            summary = "API Key error. Fallback heuristic used. Please provide GEMINI_API_KEY in .env."
            return {
                "status": status,
                "health_score": 50,
                "summary": summary,
                "reasons": ["AI analysis skipped due to missing API key."]
            }
            
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # We need to construct a rich context for the AI
        prompt = f"""
        You are an expert AI Software Archaeologist. Your task is to analyze the following GitHub repository metadata and determine if the project is "dead", "at_risk", or "healthy".
        
        Project: {repo_data.get('full_name')}
        Description: {repo_data.get('description')}
        Stars: {repo_data.get('stars')}
        Open Issues: {repo_data.get('open_issues')}
        
        Recent Releases: {json.dumps(releases_data)}
        
        Bus Factor (Core developers): {bus_factor_data.get('bus_factor')}
        High Activity Decay (Stagnation > 50% drop): {decay_data.get('is_stagnant')}
        
        Commit Semantic Analysis:
        Features: {nlp_data.get('raw_breakdown', {}).get('Features', 0)}
        Fixes: {nlp_data.get('raw_breakdown', {}).get('Fixes', 0)}
        Chores/Config: {nlp_data.get('raw_breakdown', {}).get('Chores/Config', 0)}
        
        CRITICAL REQUIREMENTS:
        1. Write the summary and reasons in {language}.
        2. Adopt a strictly ACADEMIC and OBJECTIVE tone. Do not use colloquialisms. Write as if you are publishing a peer-reviewed paper on software engineering metrics.
        
        Provide a JSON response with the following strictly formatted keys:
        - "status": One of "HEALTHY", "AT RISK", or "DEAD".
        - "health_score": An integer from 0 to 100.
        - "summary": A 2-3 sentence overarching conclusion for the project in an academic tone ({language}).
        - "reasons": An array of strings, listing 3 to 5 deeply analytical reasons based on the data provided, written in an academic tone ({language}).
        
        Return ONLY valid JSON. Wait until the end of the JSON to stop. Do not use block quotes like ```json. Just raw text starting with {{.
        """
        
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            # Clean up potential markdown formatting from the response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text)
            
        except Exception as e:
            return {
                "status": "ERROR",
                "health_score": 0,
                "summary": f"Failed to generate AI analysis: {str(e)}",
                "reasons": ["AI service exception"]
            }
