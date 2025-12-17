"""
Stracture-Master - GitHub Sync Module
GitHub repository synchronization and API integration.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RepoInfo:
    """GitHub repository information."""
    name: str
    full_name: str
    description: str
    url: str
    clone_url: str
    ssh_url: str
    private: bool
    default_branch: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    stars: int = 0
    forks: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'full_name': self.full_name,
            'description': self.description,
            'url': self.url,
            'clone_url': self.clone_url,
            'private': self.private,
            'default_branch': self.default_branch,
            'stars': self.stars,
            'forks': self.forks,
        }


@dataclass
class IssueInfo:
    """GitHub issue information."""
    number: int
    title: str
    state: str
    body: str
    author: str
    labels: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None


class GitHubSync:
    """
    GitHub synchronization and API integration.
    Requires PyGithub library.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub sync.
        
        Args:
            token: GitHub personal access token
        """
        self._token = token or os.environ.get('GITHUB_TOKEN')
        self._github = None
        self._user = None
        self._available = False
        
        if self._token:
            self._init_client()
    
    def _init_client(self) -> None:
        """Initialize GitHub client."""
        try:
            from github import Github
            self._github = Github(self._token)
            self._user = self._github.get_user()
            self._available = True
        except ImportError:
            pass
        except Exception:
            pass
    
    def is_available(self) -> bool:
        """Check if GitHub API is available."""
        return self._available
    
    def set_token(self, token: str) -> bool:
        """
        Set GitHub token.
        
        Args:
            token: Personal access token
            
        Returns:
            True if authentication successful
        """
        self._token = token
        self._init_client()
        return self._available
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user information."""
        if not self._available:
            return None
        
        try:
            return {
                'login': self._user.login,
                'name': self._user.name,
                'email': self._user.email,
                'public_repos': self._user.public_repos,
                'private_repos': self._user.total_private_repos,
                'followers': self._user.followers,
                'following': self._user.following,
            }
        except Exception:
            return None
    
    def list_repos(self, include_private: bool = True) -> List[RepoInfo]:
        """
        List user repositories.
        
        Args:
            include_private: Include private repositories
            
        Returns:
            List of RepoInfo
        """
        if not self._available:
            return []
        
        repos = []
        try:
            for repo in self._user.get_repos():
                if not include_private and repo.private:
                    continue
                
                repos.append(RepoInfo(
                    name=repo.name,
                    full_name=repo.full_name,
                    description=repo.description or '',
                    url=repo.html_url,
                    clone_url=repo.clone_url,
                    ssh_url=repo.ssh_url,
                    private=repo.private,
                    default_branch=repo.default_branch,
                    created_at=repo.created_at,
                    updated_at=repo.updated_at,
                    stars=repo.stargazers_count,
                    forks=repo.forks_count,
                ))
        except Exception:
            pass
        
        return repos
    
    def get_repo(self, repo_name: str) -> Optional[RepoInfo]:
        """
        Get repository information.
        
        Args:
            repo_name: Repository name (user/repo or just repo)
        """
        if not self._available:
            return None
        
        try:
            if '/' not in repo_name:
                repo_name = f"{self._user.login}/{repo_name}"
            
            repo = self._github.get_repo(repo_name)
            
            return RepoInfo(
                name=repo.name,
                full_name=repo.full_name,
                description=repo.description or '',
                url=repo.html_url,
                clone_url=repo.clone_url,
                ssh_url=repo.ssh_url,
                private=repo.private,
                default_branch=repo.default_branch,
                created_at=repo.created_at,
                updated_at=repo.updated_at,
                stars=repo.stargazers_count,
                forks=repo.forks_count,
            )
        except Exception:
            return None
    
    def create_repo(self, 
                    name: str, 
                    description: str = '',
                    private: bool = False,
                    auto_init: bool = True) -> Optional[RepoInfo]:
        """
        Create a new repository.
        
        Args:
            name: Repository name
            description: Repository description
            private: Make private
            auto_init: Initialize with README
            
        Returns:
            RepoInfo or None
        """
        if not self._available:
            return None
        
        try:
            repo = self._user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=auto_init
            )
            
            return RepoInfo(
                name=repo.name,
                full_name=repo.full_name,
                description=repo.description or '',
                url=repo.html_url,
                clone_url=repo.clone_url,
                ssh_url=repo.ssh_url,
                private=repo.private,
                default_branch=repo.default_branch,
            )
        except Exception:
            return None
    
    def upload_file(self, 
                    repo_name: str,
                    file_path: str,
                    content: str,
                    message: str = 'Update file',
                    branch: Optional[str] = None) -> bool:
        """
        Upload or update a file in repository.
        
        Args:
            repo_name: Repository name
            file_path: Path in repository
            content: File content
            message: Commit message
            branch: Branch name
        """
        if not self._available:
            return False
        
        try:
            if '/' not in repo_name:
                repo_name = f"{self._user.login}/{repo_name}"
            
            repo = self._github.get_repo(repo_name)
            
            # Check if file exists
            try:
                existing = repo.get_contents(file_path, ref=branch)
                repo.update_file(
                    file_path,
                    message,
                    content,
                    existing.sha,
                    branch=branch
                )
            except:
                repo.create_file(
                    file_path,
                    message,
                    content,
                    branch=branch
                )
            
            return True
        except Exception:
            return False
    
    def download_file(self, 
                      repo_name: str,
                      file_path: str,
                      branch: Optional[str] = None) -> Optional[str]:
        """
        Download a file from repository.
        
        Args:
            repo_name: Repository name
            file_path: Path in repository
            branch: Branch name
            
        Returns:
            File content or None
        """
        if not self._available:
            return None
        
        try:
            if '/' not in repo_name:
                repo_name = f"{self._user.login}/{repo_name}"
            
            repo = self._github.get_repo(repo_name)
            content = repo.get_contents(file_path, ref=branch)
            
            return content.decoded_content.decode('utf-8')
        except Exception:
            return None
    
    def create_issue(self,
                     repo_name: str,
                     title: str,
                     body: str = '',
                     labels: Optional[List[str]] = None) -> Optional[int]:
        """
        Create an issue.
        
        Returns:
            Issue number or None
        """
        if not self._available:
            return None
        
        try:
            if '/' not in repo_name:
                repo_name = f"{self._user.login}/{repo_name}"
            
            repo = self._github.get_repo(repo_name)
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=labels or []
            )
            
            return issue.number
        except Exception:
            return None
    
    def list_issues(self, 
                    repo_name: str,
                    state: str = 'open') -> List[IssueInfo]:
        """
        List repository issues.
        
        Args:
            repo_name: Repository name
            state: 'open', 'closed', or 'all'
        """
        if not self._available:
            return []
        
        issues = []
        try:
            if '/' not in repo_name:
                repo_name = f"{self._user.login}/{repo_name}"
            
            repo = self._github.get_repo(repo_name)
            
            for issue in repo.get_issues(state=state):
                issues.append(IssueInfo(
                    number=issue.number,
                    title=issue.title,
                    state=issue.state,
                    body=issue.body or '',
                    author=issue.user.login,
                    labels=[l.name for l in issue.labels],
                    created_at=issue.created_at,
                ))
        except Exception:
            pass
        
        return issues
    
    def sync_structure(self, 
                       repo_name: str,
                       structure: Dict[str, Any],
                       branch: Optional[str] = None) -> bool:
        """
        Sync project structure to GitHub.
        
        Args:
            repo_name: Repository name
            structure: Structure dictionary
            branch: Branch name
        """
        content = json.dumps(structure, indent=2, ensure_ascii=False)
        return self.upload_file(
            repo_name,
            '.Stracture-Master/structure.json',
            content,
            'Update project structure',
            branch
        )


# Singleton instance
github_sync = GitHubSync()
