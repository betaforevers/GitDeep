from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

class FileMetricsEngine:
    def __init__(self):
        pass

    def calculate_file_metrics(self, commits: List[Dict[str, Any]]) -> dict:
        """
        Calculates advanced file-level metrics including Ownership, Rhythm, Structure, and Coupling.
        """
        if not commits:
            return {"hotspots": [], "legacy_candidates": [], "bug_prone": [], "ownership_risks": [], "tags": {}}

        file_stats = defaultdict(lambda: {
            "first_seen": None,
            "last_seen": None,
            "changes": 0,
            "added": 0,
            "deleted": 0,
            "commit_count": 0,
            "authors": defaultdict(int), # changes per author
            "weekend_commits": 0,
            "night_commits": 0,
            "prod_file": False,
            "test_file": False
        })
        
        # Track co-changes for coupling
        co_changes = defaultdict(lambda: defaultdict(int))

        for commit in reversed(commits): # reverse to process chronological
            commit_date = commit.get("date")
            author = commit.get("author", "Unknown")
            if not commit_date: continue
            
            try:
                dt = datetime.fromisoformat(commit_date.replace(" ", "T", 1).replace(" +", "+").replace(" -", "-"))
                is_weekend = dt.weekday() >= 5
                is_night = dt.hour < 6 or dt.hour > 20
            except:
                is_weekend = False
                is_night = False
                try:
                    dt = datetime.fromisoformat(commit_date)
                except:
                    continue

            files_in_commit = [f.get("filename") for f in commit.get("files", []) if f.get("filename")]
            
            # Record coupling
            for i, f1 in enumerate(files_in_commit):
                for f2 in files_in_commit[i+1:]:
                    if f1 != f2:
                        # Sort to keep direction consistent
                        pair = tuple(sorted([f1, f2]))
                        co_changes[pair[0]][pair[1]] += 1

            for file in commit.get("files", []):
                filename = file.get("filename")
                if not filename: continue
                
                changes = file.get("changes", 0)
                added = file.get("added", 0)
                deleted = file.get("deleted", 0)

                stats = file_stats[filename]
                
                if stats["first_seen"] is None or dt < stats["first_seen"]:
                    stats["first_seen"] = dt
                if stats["last_seen"] is None or dt > stats["last_seen"]:
                    stats["last_seen"] = dt
                
                stats["changes"] += changes
                stats["added"] += added
                stats["deleted"] += deleted
                stats["commit_count"] += 1
                stats["authors"][author] += changes
                
                if is_weekend: stats["weekend_commits"] += 1
                if is_night: stats["night_commits"] += 1
                
                fname_lower = filename.lower()
                if "test" in fname_lower or "spec" in fname_lower:
                    stats["test_file"] = True
                elif filename.endswith((".py", ".js", ".ts", ".java", ".go", ".c", ".cpp", ".cs")):
                    stats["prod_file"] = True

        # Flatten and calculate derived metrics
        results = []
        tags = defaultdict(list)
        
        for filename, stats in file_stats.items():
            first = stats["first_seen"]
            last = stats["last_seen"]
            
            if not first or not last: continue
                
            age_days = (last - first).days
            frequency_days = age_days / stats["commit_count"] if stats["commit_count"] > 1 else -1

            # Determine Primary Owner and Bus Factor Risk
            total_author_changes = sum(stats["authors"].values())
            primary_owner = "Unknown"
            ownership_pct = 0
            if total_author_changes > 0:
                top_author = max(stats["authors"].items(), key=lambda x: x[1])
                primary_owner = top_author[0]
                ownership_pct = (top_author[1] / total_author_changes) * 100
                
            net_growth = stats["added"] - stats["deleted"]

            result = {
                "filename": filename,
                "changes": stats["changes"],
                "added": stats["added"],
                "deleted": stats["deleted"],
                "net_growth": net_growth,
                "commit_count": stats["commit_count"],
                "first_seen": first.isoformat(),
                "last_seen": last.isoformat(),
                "age_days": age_days,
                "frequency_days": frequency_days,
                "primary_owner": primary_owner,
                "ownership_pct": ownership_pct,
                "weekend_pct": (stats["weekend_commits"] / stats["commit_count"] * 100) if stats["commit_count"] > 0 else 0,
                "night_pct": (stats["night_commits"] / stats["commit_count"] * 100) if stats["commit_count"] > 0 else 0,
                "is_test": stats["test_file"],
                "is_prod": stats["prod_file"]
            }
            results.append(result)

        # --- Sub-categories & Classification ---
        
        valid_results = [r for r in results if r["commit_count"] > 1] # Ignore one-off files
        
        # 1. Hotspots (High commit count & changes)
        hotspots = sorted(valid_results, key=lambda x: (x["commit_count"], x["changes"]), reverse=True)[:5]
        for h in hotspots: tags[h['filename']].append("Hotspot")
        
        # 2. Bug Prone (Small changes but highly frequent)
        bug_candidates = [r for r in valid_results if r["commit_count"] >= 3]
        bug_prone = sorted(bug_candidates, key=lambda x: x["changes"] / x["commit_count"])[:5]
        for b in bug_prone: tags[b['filename']].append("Bug-Prone")
        
        # 3. Legacy / Dead Files
        legacy_candidates = sorted([r for r in valid_results if r["age_days"] > 30], key=lambda x: x["last_seen"])[:5]
        for l in legacy_candidates: tags[l['filename']].append("Legacy")
            
        # 4. Single-Owner Dependency (Bus Factor Risk)
        # Prod files that heavily rely on 1 person and have significant changes
        ownership_risks = [r for r in valid_results if r["is_prod"] and r["ownership_pct"] >= 80 and r["changes"] > 50]
        ownership_risks = sorted(ownership_risks, key=lambda x: x["changes"], reverse=True)[:5]
        for o in ownership_risks: tags[o['filename']].append("Single-Owner Risk 👤")
        
        # 5. Technical Debt / Inflation
        # Files that grow constantly without much deletion
        inflation_risks = [r for r in valid_results if r["is_prod"] and r["net_growth"] > 200 and r["deleted"] < (r["added"] * 0.1)]
        inflation_risks = sorted(inflation_risks, key=lambda x: x["net_growth"], reverse=True)[:5]
        for i in inflation_risks: tags[i['filename']].append("Bloated 📈")

        #6. Night Owl
        night_owls = [r for r in valid_results if r["night_pct"] > 50]
        night_owls = sorted(night_owls, key=lambda x: x["night_pct"], reverse=True)[:5]
        for n in night_owls: tags[n['filename']].append("Night Owl 🦉")

        #7. Weekend Warrior
        weekend_warriors = [r for r in valid_results if r["weekend_pct"] > 50]
        weekend_warriors = sorted(weekend_warriors, key=lambda x: x["weekend_pct"], reverse=True)[:5]
        for w in weekend_warriors: tags[w['filename']].append("Weekend Warrior 🍻")

        #8. Test Files
        test_files = [r for r in valid_results if r["is_test"]]
        test_files = sorted(test_files, key=lambda x: x["changes"], reverse=True)[:5]
        for t in test_files: tags[t['filename']].append("Test File 🧪")

        #9. Prod Files
        prod_files = [r for r in valid_results if r["is_prod"]]
        prod_files = sorted(prod_files, key=lambda x: x["changes"], reverse=True)[:5]
        for p in prod_files: tags[p['filename']].append("Prod File 🏭")
        
        # Classify Healthy
        for r in valid_results:
            if not tags[r['filename']] and r["is_prod"]:
                tags[r['filename']].append("Healthy 🟢")

        # Top Coupled Files
        top_coupled = []
        for f1, deps in co_changes.items():
            for f2, count in deps.items():
                if count >= 3: # threshold
                    top_coupled.append({"file1": f1, "file2": f2, "co_commits": count})
        top_coupled = sorted(top_coupled, key=lambda x: x["co_commits"], reverse=True)[:5]

        return {
            "hotspots": hotspots,
            "bug_prone": bug_prone,
            "legacy_candidates": legacy_candidates,
            "ownership_risks": ownership_risks,
            "inflation_risks": inflation_risks,
            "night_owls": night_owls,
            "weekend_warriors": weekend_warriors,
            "test_files": test_files,
            "prod_files": prod_files,
            "top_coupled": top_coupled,
            "total_files_tracked": len(results),
            "tags": dict(tags)
        }
