import os
from github import Github
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("GITHUB_PAT")
g = Github(token)
repo = g.get_repo("betaforevers/GitDeep")
commits = repo.get_commits()
count = 0
for c in commits:
    print(f"Commit: {c.sha}")
    # c.files requires an API call per commit!
    for f in c.files:
        print(f"  File: {f.filename} (changes: {f.changes}, status: {f.status})")
    count += 1
    if count >= 2: break
