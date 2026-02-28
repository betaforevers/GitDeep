import json
import google.generativeai as genai
from app.core.config import settings

class ReasoningEngine:
    def synthesize_report(self, repo_data: dict, bus_factor_data: dict, decay_data: dict, nlp_data: dict, releases_data: list, file_metrics_data: dict, language: str = "English") -> dict:
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
        
        # Extract advanced file metrics for the prompt
        legacy_files = [f['filename'] for f in file_metrics_data.get('legacy_candidates', [])]
        bug_prone = [f['filename'] for f in file_metrics_data.get('bug_prone', [])]
        hotspots = [f['filename'] for f in file_metrics_data.get('hotspots', [])]
        bus_factor_files = [f['filename'] for f in file_metrics_data.get('ownership_risks', [])]
        bloated_files = [f['filename'] for f in file_metrics_data.get('inflation_risks', [])]
        coupled_pairs = [f"{c['file1']} & {c['file2']} ({c['co_commits']} times)" for c in file_metrics_data.get('top_coupled', [])]
        
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
        
        Advanced File-Level Analytics & Rhythm:
        - Legacy Files (Dormant): {', '.join(legacy_files) if legacy_files else 'None detected'}
        - Bug-Prone (Micro-commits): {', '.join(bug_prone) if bug_prone else 'None detected'}
        - Refactor Hotspots: {', '.join(hotspots) if hotspots else 'None detected'}
        - High Bus-Factor Files (Single owner >80%): {', '.join(bus_factor_files) if bus_factor_files else 'None detected'}
        - Bloated Files (High net growth, low deletion): {', '.join(bloated_files) if bloated_files else 'None detected'}
        - Highly Coupled Files (Edited together): {', '.join(coupled_pairs) if coupled_pairs else 'None detected'}
        
        CRITICAL REQUIREMENTS:
        1. Write the summary and reasons in {language}.
        2. Adopt a strictly ACADEMIC and OBJECTIVE tone. Do not use colloquialisms. Write as if you are publishing a peer-reviewed paper on software engineering metrics.
        3. Specifically mention the file-level health (e.g. single-owner risks, bloated files, highly coupled pairs, bug-prone areas) in your analytical reasons if they pose a risk. Use this data to diagnose structural decay.
        
        Provide a JSON response with the following strictly formatted keys:
        - "status": One of "HEALTHY", "AT RISK", or "DEAD".
        - "health_score": An integer from 0 to 100.
        - "summary": A 2-3 sentence overarching conclusion for the project in an academic tone ({language}).
        - "reasons": An array of strings, listing 3 to 5 deeply analytical reasons based on the data provided, written in an academic tone ({language}). Discuss the rhythm and file risks directly if present.
        
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
