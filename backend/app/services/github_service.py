from github import Github
from app.core.config import settings

class GitHubService:
    def __init__(self):
        # Authenticate using token if available, otherwise unauthenticated (lower rate limit)
        if settings.GITHUB_PAT:
            self.g = Github(settings.GITHUB_PAT, retry=0)
        else:
            self.g = Github(retry=0)

    def get_repo_info(self, owner: str, repo_name: str) -> dict:
        full_name = f"{owner}/{repo_name}"
        repo = self.g.get_repo(full_name)
        
        return {
            "full_name": repo.full_name,
            "description": repo.description,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat(),
            "pushed_at": repo.pushed_at.isoformat()
        }

    def get_recent_commits(self, owner: str, repo_name: str, limit: int = 100) -> list:
        full_name = f"{owner}/{repo_name}"
        repo = self.g.get_repo(full_name)
        
        commits_data = []
        commits = repo.get_commits()
        
        count = 0
        for commit in commits:
            if count >= limit:
                break
                
            author_name = commit.commit.author.name if commit.commit.author else "Unknown"
            date_str = commit.commit.author.date.isoformat() if commit.commit.author else ""
            
            commits_data.append({
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": author_name,
                "date": date_str
            })
            count += 1
            
        return commits_data

    def get_recent_releases(self, owner: str, repo_name: str, limit: int = 10) -> list:
        full_name = f"{owner}/{repo_name}"
        repo = self.g.get_repo(full_name)
        
        releases_data = []
        releases = repo.get_releases()
        
        count = 0
        for rel in releases:
            if count >= limit:
                break
                
            releases_data.append({
                "tag_name": rel.tag_name,
                "name": rel.title,
                "published_at": rel.published_at.isoformat() if rel.published_at else "",
                "author": rel.author.login if rel.author else "Unknown"
            })
            count += 1
            
        return releases_data
