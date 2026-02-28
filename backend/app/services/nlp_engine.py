import re
from typing import List, Dict, Any

class NLPEngine:
    def __init__(self):
        # Very basic heuristics for commit intentions
        self.feature_keywords = [r'\bfeat\b', r'\bfeature\b', r'\badd\b', r'\bnew\b']
        self.fix_keywords = [r'\bfix\b', r'\bpatch\b', r'\bbug\b', r'\bresolve\b']
        self.chore_keywords = [r'\bchore\b', r'\bconfig\b', r'\bbuild\b', r'\bci\b', r'\btest\b']
        self.docs_keywords = [r'\bdoc\b', r'\bdocs\b', r'\breadme\b']

    def analyze_commits(self, commits: List[Dict[str, Any]]) -> dict:
        """
        Analyzes the semantic intent of recent commits using regex heuristics.
        Returns a breakdown of intent types.
        """
        metrics = {
            "feature": 0,
            "fix": 0,
            "chore": 0,
            "docs": 0,
            "other": 0
        }
        
        for commit in commits:
            msg = commit.get("message", "").lower()
            
            if any(re.search(kw, msg) for kw in self.feature_keywords):
                metrics["feature"] += 1
            elif any(re.search(kw, msg) for kw in self.fix_keywords):
                metrics["fix"] += 1
            elif any(re.search(kw, msg) for kw in self.chore_keywords):
                metrics["chore"] += 1
            elif any(re.search(kw, msg) for kw in self.docs_keywords):
                metrics["docs"] += 1
            else:
                metrics["other"] += 1
                
        total = len(commits)
        if total == 0:
            return metrics
            
        # Calculate Technical Debt Ratio (ratio of fixes and chores vs features)
        maintenance_work = metrics["fix"] + metrics["chore"]
        feature_work = metrics["feature"]
        
        # Avoid division by zero
        if feature_work == 0:
            tech_debt_ratio = maintenance_work
        else:
            tech_debt_ratio = maintenance_work / feature_work
            
        metrics["tech_debt_ratio"] = round(tech_debt_ratio, 2)
        metrics["maintenance_focus"] = (maintenance_work / total) > 0.6
        metrics["raw_breakdown"] = {
            "Features": metrics["feature"],
            "Fixes": metrics["fix"],
            "Chores/Config": metrics["chore"],
            "Docs": metrics["docs"],
            "Other": metrics["other"]
        }
        
        return metrics
