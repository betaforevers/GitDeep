from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

class FileMetricsEngine:
    def __init__(self):
        pass

    def calculate_file_metrics(self, commits: List[Dict[str, Any]]) -> dict:
        """
        Calculates file-level metrics from a list of commits that include file data.
        Returns hotspots and change density insights.
        """
        if not commits:
            return {"hotspots": [], "legacy_candidates": [], "bug_prone": []}

        file_stats = defaultdict(lambda: {
            "first_seen": None,
            "last_seen": None,
            "changes": 0,
            "commit_count": 0
        })

        for commit in reversed(commits): # reverse to process chronological
            commit_date = commit.get("date")
            if not commit_date: continue
            
            try:
                # Local git format from `git log --date=iso`: 2024-05-18 14:32:00 +0000
                # or string depending on format
                dt = datetime.fromisoformat(commit_date.replace(" ", "T", 1).replace(" +", "+").replace(" -", "-"))
            except:
                try:
                    dt = datetime.fromisoformat(commit_date)
                except:
                    continue

            for file in commit.get("files", []):
                filename = file.get("filename")
                changes = file.get("changes", 0)

                stats = file_stats[filename]
                
                if stats["first_seen"] is None or dt < stats["first_seen"]:
                    stats["first_seen"] = dt
                if stats["last_seen"] is None or dt > stats["last_seen"]:
                    stats["last_seen"] = dt
                
                stats["changes"] += changes
                stats["commit_count"] += 1

        # Flatten and calculate derived metrics
        results = []
        for filename, stats in file_stats.items():
            first = stats["first_seen"]
            last = stats["last_seen"]
            
            # Safe defaults just in case
            if not first or not last: continue
                
            age_days = (last - first).days
            frequency_days = age_days / stats["commit_count"] if stats["commit_count"] > 1 else -1

            results.append({
                "filename": filename,
                "changes": stats["changes"],
                "commit_count": stats["commit_count"],
                "first_seen": first.isoformat(),
                "last_seen": last.isoformat(),
                "age_days": age_days,
                "frequency_days": frequency_days
            })

        # --- Sub-categories ---
        
        # 1. Hotspots / Refactor Candidates (High commit count, high changes)
        hotspots = sorted(results, key=lambda x: (x["commit_count"], x["changes"]), reverse=True)[:5]
        
        # 2. Bug Prone (Small changes but highly frequent - lots of micro-commits)
        # Filter files updated at least 3 times. We look for lowest changes per commit ratio.
        bug_prone = [r for r in results if r["commit_count"] >= 3]
        bug_prone = sorted(bug_prone, key=lambda x: x["changes"] / x["commit_count"])[:5]
        
        # 3. Legacy Candidates / Dead Files (Within the window: touched long ago, but not recently)
        # We sort by oldest 'last_seen'.
        legacy_candidates = sorted([r for r in results if r["age_days"] > 0], key=lambda x: x["last_seen"])[:5]

        return {
            "hotspots": hotspots,
            "bug_prone": bug_prone,
            "legacy_candidates": legacy_candidates,
            "total_files_tracked": len(results)
        }
