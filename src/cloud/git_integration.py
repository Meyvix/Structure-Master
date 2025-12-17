"""
Stracture-Master - Git Integration Module
Local Git repository management and operations.
"""

import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CommitInfo:
    """Information about a git commit."""
    hash: str
    short_hash: str
    author: str
    email: str
    date: datetime
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'hash': self.hash,
            'short_hash': self.short_hash,
            'author': self.author,
            'email': self.email,
            'date': self.date.isoformat(),
            'message': self.message,
        }


@dataclass
class BranchInfo:
    """Information about a git branch."""
    name: str
    is_current: bool
    last_commit: Optional[str] = None
    tracking: Optional[str] = None


@dataclass
class GitStatus:
    """Git repository status."""
    is_repo: bool = False
    branch: str = ''
    is_clean: bool = True
    modified: List[str] = field(default_factory=list)
    staged: List[str] = field(default_factory=list)
    untracked: List[str] = field(default_factory=list)
    ahead: int = 0
    behind: int = 0


class GitIntegration:
    """
    Git repository integration for local operations.
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize Git integration.
        
        Args:
            repo_path: Path to git repository
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self._git_available = self._check_git_available()
    
    def _check_git_available(self) -> bool:
        """Check if git command is available."""
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _run_git(self, *args, cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
        """
        Run a git command.
        
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                ['git'] + list(args),
                capture_output=True,
                text=True,
                cwd=cwd or self.repo_path
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, '', str(e)
    
    def is_git_repo(self, path: Optional[Path] = None) -> bool:
        """Check if path is a git repository."""
        check_path = path or self.repo_path
        return (check_path / '.git').is_dir()
    
    def init(self, path: Optional[Path] = None) -> bool:
        """
        Initialize a new git repository.
        
        Args:
            path: Path to initialize (default: repo_path)
            
        Returns:
            True if successful
        """
        target = path or self.repo_path
        success, _, _ = self._run_git('init', cwd=target)
        return success
    
    def get_status(self) -> GitStatus:
        """Get repository status."""
        status = GitStatus()
        
        if not self.is_git_repo():
            return status
        
        status.is_repo = True
        
        # Get current branch
        success, branch, _ = self._run_git('branch', '--show-current')
        if success:
            status.branch = branch
        
        # Get status
        success, output, _ = self._run_git('status', '--porcelain')
        if success and output:
            status.is_clean = False
            for line in output.split('\n'):
                if not line:
                    continue
                state = line[:2]
                file_path = line[3:]
                
                if state[0] in 'MADRCU':
                    status.staged.append(file_path)
                if state[1] in 'MDRU':
                    status.modified.append(file_path)
                if state == '??':
                    status.untracked.append(file_path)
        else:
            status.is_clean = True
        
        # Get ahead/behind
        success, output, _ = self._run_git('rev-list', '--left-right', '--count', 'HEAD...@{upstream}')
        if success and output:
            parts = output.split('\t')
            if len(parts) == 2:
                status.ahead = int(parts[0])
                status.behind = int(parts[1])
        
        return status
    
    def get_branches(self) -> List[BranchInfo]:
        """Get list of branches."""
        branches = []
        
        success, output, _ = self._run_git('branch', '-a', '--format=%(refname:short)|%(HEAD)|%(upstream:short)')
        if success:
            for line in output.split('\n'):
                if not line:
                    continue
                parts = line.split('|')
                branches.append(BranchInfo(
                    name=parts[0],
                    is_current=parts[1] == '*',
                    tracking=parts[2] if len(parts) > 2 and parts[2] else None
                ))
        
        return branches
    
    def get_commit_history(self, limit: int = 50) -> List[CommitInfo]:
        """
        Get commit history.
        
        Args:
            limit: Maximum number of commits
            
        Returns:
            List of CommitInfo
        """
        commits = []
        
        format_str = '%H|%h|%an|%ae|%aI|%s'
        success, output, _ = self._run_git('log', f'-{limit}', f'--format={format_str}')
        
        if success:
            for line in output.split('\n'):
                if not line:
                    continue
                parts = line.split('|', 5)
                if len(parts) >= 6:
                    commits.append(CommitInfo(
                        hash=parts[0],
                        short_hash=parts[1],
                        author=parts[2],
                        email=parts[3],
                        date=datetime.fromisoformat(parts[4]),
                        message=parts[5]
                    ))
        
        return commits
    
    def add(self, paths: Optional[List[str]] = None) -> bool:
        """
        Stage files for commit.
        
        Args:
            paths: List of paths to add (default: all)
        """
        if paths:
            success, _, _ = self._run_git('add', *paths)
        else:
            success, _, _ = self._run_git('add', '-A')
        return success
    
    def commit(self, message: str, author: Optional[str] = None) -> bool:
        """
        Create a commit.
        
        Args:
            message: Commit message
            author: Optional author (format: "Name <email>")
        """
        args = ['commit', '-m', message]
        if author:
            args.extend(['--author', author])
        
        success, _, _ = self._run_git(*args)
        return success
    
    def push(self, remote: str = 'origin', branch: Optional[str] = None) -> bool:
        """Push to remote."""
        args = ['push', remote]
        if branch:
            args.append(branch)
        
        success, _, _ = self._run_git(*args)
        return success
    
    def pull(self, remote: str = 'origin', branch: Optional[str] = None) -> bool:
        """Pull from remote."""
        args = ['pull', remote]
        if branch:
            args.append(branch)
        
        success, _, _ = self._run_git(*args)
        return success
    
    def checkout(self, branch: str, create: bool = False) -> bool:
        """
        Checkout a branch.
        
        Args:
            branch: Branch name
            create: Create branch if not exists
        """
        args = ['checkout']
        if create:
            args.append('-b')
        args.append(branch)
        
        success, _, _ = self._run_git(*args)
        return success
    
    def create_tag(self, name: str, message: Optional[str] = None) -> bool:
        """Create a tag."""
        args = ['tag']
        if message:
            args.extend(['-a', name, '-m', message])
        else:
            args.append(name)
        
        success, _, _ = self._run_git(*args)
        return success
    
    def get_diff(self, staged: bool = False) -> str:
        """Get diff output."""
        args = ['diff']
        if staged:
            args.append('--staged')
        
        success, output, _ = self._run_git(*args)
        return output if success else ''
    
    def get_remote_url(self, remote: str = 'origin') -> Optional[str]:
        """Get remote URL."""
        success, output, _ = self._run_git('remote', 'get-url', remote)
        return output if success else None
    
    def add_remote(self, name: str, url: str) -> bool:
        """Add a remote."""
        success, _, _ = self._run_git('remote', 'add', name, url)
        return success
    
    def is_available(self) -> bool:
        """Check if Git is available."""
        return self._git_available


# Singleton instance
git = GitIntegration()
