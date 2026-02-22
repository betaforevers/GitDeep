import os
import subprocess
import shutil
import uuid
from typing import List, Dict, Any

class GitAnalyzer:
    def __init__(self):
        self.tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tmp")
        os.makedirs(self.tmp_dir, exist_ok=True)
        
    def clone_and_extract_file_history(self, git_url: str) -> List[Dict[str, Any]]:
        """
        Clones the repo locally (bare clone for speed), extracts file history, and returns it.
        Then deletes the clone.
        """
        # Create unique directory
        repo_id = str(uuid.uuid4())
        clone_path = os.path.join(self.tmp_dir, repo_id)
        
        try:
            # 1. Clone Repo (--bare is faster, no working tree needed for logs)
            subprocess.run(
                ["git", "clone", "--bare", "--filter=blob:none", git_url, clone_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60 # Prevent hanging on massive repos
            )
            
            # 2. Extract git log
            # We want: commit|date|author\n file_changes...
            # Format: ^CF^ (delimiter) %H (hash) %cI (iso date) 
            log_format = "^CF^%H|%cI"
            
            result = subprocess.run(
                ["git", "log", f"--format={log_format}", "--name-status"],
                cwd=clone_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=30 # Don't parse linux kernel
            )
            
            return self._parse_git_log(result.stdout)
            
        except Exception as e:
            # Silently log/ignore for now, fallback will be empty metrics
            print(f"Git Analyzer Error: {e}")
            return []
        finally:
            # 3. Cleanup
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path, ignore_errors=True)
                
    def _parse_git_log(self, log_output: str) -> List[Dict[str, Any]]:
        """
        Parses output from `git log --format=^CF^%H|%cI --name-status`
        Returns a list of commit dictionaries with file status.
        (We don't need changes/lines modified for hotspot calculation if we have frequent commits,
         but we could try to use --numstat instead of --name-status if needed.
         Since user asked to just view the files, frequency is usually enough.)
         
         We will use --numstat if we want 'changes', but name-status is faster. Let's start with just tracking edits.
        """
        commits = []
        current_commit = None
        
        for line in log_output.split("\n"):
            line = line.strip()
            if not line: continue
            
            if line.startswith("^CF^"):
                # New commit block
                parts = line[4:].split("|")
                if len(parts) >= 2:
                    current_commit = {
                        "sha": parts[0],
                        "date": parts[1],
                        "files": []
                    }
                    commits.append(current_commit)
            else:
                # File change line (e.g., M file.py OR A file.py OR D file.py)
                if current_commit:
                    parts = line.split(maxsplit=1)
                    if len(parts) >= 2:
                        status = parts[0]
                        filename = parts[1]
                        
                        # We just track that it was modified (changes=1 as a baseline since --numstat is slow)
                        # We might refine this to use --numstat if exact lines are needed.
                        current_commit["files"].append({
                            "filename": filename,
                            "status": status,
                            "changes": 1 # Placeholder for frequency count
                        })
        
        return commits
