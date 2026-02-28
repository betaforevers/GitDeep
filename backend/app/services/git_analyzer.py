import os
import subprocess
import shutil
import uuid
from typing import List, Dict, Any
from app.core.config import settings

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
        
        # Inject PAT to avoid hanging on private repos
        auth_url = git_url
        if settings.GITHUB_PAT and git_url.startswith("https://"):
            auth_url = git_url.replace("https://", f"https://{settings.GITHUB_PAT}@")
            
        try:
            # 1. Clone Repo (--bare is faster, no working tree needed for logs)
            # Use env vars to strictly disable any interactive prompts
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"
            env["GIT_ASKPASS"] = "echo"
            env["SSH_ASKPASS"] = "echo"

            subprocess.run(
                ["git", "clone", "--bare", "--filter=blob:none", auth_url, clone_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60, # Prevent hanging on massive repos
                env=env
            )
            
            # 2. Extract git log
            # We want: commit|date|author\n file_changes...
            # Format: ^CF^ (delimiter) %H (hash) %cI (iso date) %an (author name)
            log_format = "^CF^%H|%cI|%an"
            
            result = subprocess.run(
                ["git", "log", f"--format={log_format}", "--numstat"],
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
        Parses output from `git log --format=^CF^%H|%cI|%an --numstat`
        Returns a list of commit dictionaries with file stats.
        """
        commits = []
        current_commit = None
        
        for line in log_output.split("\n"):
            line = line.strip()
            if not line: continue
            
            if line.startswith("^CF^"):
                # New commit block
                parts = line[4:].split("|")
                if len(parts) >= 3:
                    current_commit = {
                        "sha": parts[0],
                        "date": parts[1],
                        "author": parts[2],
                        "files": []
                    }
                    commits.append(current_commit)
            else:
                # File change line using --numstat (e.g., 10\t5\tfile.py)
                if current_commit:
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        added = parts[0]
                        deleted = parts[1]
                        filename = parts[2]
                        
                        # Handle binary files which show '-' instead of numbers
                        add_count = int(added) if added.isdigit() else 0
                        del_count = int(deleted) if deleted.isdigit() else 0
                        
                        current_commit["files"].append({
                            "filename": filename,
                            "added": add_count,
                            "deleted": del_count,
                            "changes": add_count + del_count
                        })
        
        return commits
