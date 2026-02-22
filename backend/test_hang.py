import sys
from app.services.github_service import GitHubService
try:
    github_service = GitHubService()
    print("Getting repo")
    repo = github_service.g.get_repo("betaforevers/GitDeep")
    print("Getting commits")
    commits = repo.get_commits()
    print("Iterating")
    for _ in commits:
        break
    print("Done")
except Exception as e:
    print(f"Error: {e}")
