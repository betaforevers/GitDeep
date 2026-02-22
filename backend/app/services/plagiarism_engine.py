import os
import glob
import json
import logging
from typing import Dict, Any, Tuple
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class PlagiarismEngine:
    def __init__(self, tmp_dir: str):
        self.tmp_dir = tmp_dir
        
    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    def _get_file_tokens(self, filepath: str) -> set:
        """Reads a file and returns a set of unique lines/tokens (stripped of whitespace)."""
        tokens = set()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    if len(stripped) > 5:  # Ignore very short lines like "}", "return"
                        tokens.add(stripped)
        except Exception:
            pass # Ignore binary or undecodable files
        return tokens

    def calculate_internal_duplication(self, clone_path: str) -> Tuple[float, list]:
        """
        Scans all source code files in the directory and computes pairwise Jaccard similarity.
        Returns the overall duplication percentage and a list of the most duplicated file pairs.
        """
        if not os.path.exists(clone_path):
            return 0.0, []

        # Find all code files (exclude tests, vendor, node_modules, etc. if possible, but keep it simple for now)
        code_extensions = {'.py', '.js', '.ts', '.java', '.go', '.c', '.cpp', '.cs', '.php', '.rb', '.swift', '.kt'}
        files_to_check = []
        
        for root, dirs, files in os.walk(clone_path):
            # Skip hidden dirs and common dependency folders
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'venv', 'env', 'dist', 'build', 'vendor')]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in code_extensions:
                    files_to_check.append(os.path.join(root, file))

        # Too many files = too slow for O(N^2) pairwise comparison. Cap it.
        if len(files_to_check) > 300:
            files_to_check = files_to_check[:300]

        file_data = {}
        for f in files_to_check:
            tokens = self._get_file_tokens(f)
            if len(tokens) > 10:  # Only compare files with meaningful content
                rel_path = os.path.relpath(f, clone_path)
                file_data[rel_path] = tokens

        high_duplication_pairs = []
        total_similarity = 0.0
        comparisons = 0

        filenames = list(file_data.keys())
        for i in range(len(filenames)):
            for j in range(i + 1, len(filenames)):
                f1 = filenames[i]
                f2 = filenames[j]
                
                sim = self._jaccard_similarity(file_data[f1], file_data[f2])
                if sim > 0:
                    total_similarity += sim
                    comparisons += 1
                
                if sim > 0.4:  # > 40% similar is highly suspect
                    high_duplication_pairs.append({
                        "file1": f1,
                        "file2": f2,
                        "similarity": round(sim * 100, 1)
                    })

        avg_duplication = (total_similarity / comparisons * 100) if comparisons > 0 else 0.0
        high_duplication_pairs = sorted(high_duplication_pairs, key=lambda x: x['similarity'], reverse=True)[:5]

        return round(avg_duplication, 1), high_duplication_pairs

    def check_external_originality(self, repo_data: dict, clone_path: str, top_files: list, language: str = "English") -> dict:
        """
        Uses Gemini to analyze the repository context and top active files to determine if it's
        highly original, a tutorial clone, or just boilerplate.
        """
        if not settings.GEMINI_API_KEY:
             return {
                "score": 0,
                "assessment": "Unknown (No API Key)",
                "explanation": "Cannot perform external originality check without Gemini API Key."
            }

        # Try to read contents of the top 3 hotspots
        file_samples = ""
        for hp in top_files[:3]:
            fname = hp['filename']
            full_path = os.path.join(clone_path, fname)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()[:2000] # Take first 2000 chars to avoid token limits
                    file_samples += f"\n--- {fname} ---\n{content}\n"
                except:
                    pass

        prompt = f"""
        You are an expert Software Auditor detecting plagiarism and assessing code originality.
        Analyze the following GitHub repository and code samples to determine if this project represents original software engineering work, or if it appears to be a copy-paste job, a standard framework boilerplate, or a common tutorial clone (e.g., standard "To-Do app" or "Blogging engine").
        
        Repository Name: {repo_data.get('full_name')}
        Description: {repo_data.get('description')}
        
        Code Samples from Core Files:
        {file_samples}
        
        Please provide your assessment strictly in {language}.
        
        Return ONLY a JSON object with the following keys:
        - "score": An integer from 0 to 100 (100 = Highly original architecture/logic, 0 = 100% boilerplate/tutorial copy).
        - "assessment": A short 3-4 word classification (e.g. "Highly Original", "Tutorial Clone", "Standard Boilerplate").
        - "explanation": A 2 sentence explanation of your reasoning.
        """

        genai.configure(api_key=settings.GEMINI_API_KEY)
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            logger.error(f"External Plagiarism Check failed: {e}")
            return {
                "score": 0,
                "assessment": "Error",
                "explanation": "Failed to generate originality score via AI."
            }
