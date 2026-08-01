#!/usr/bin/env python3
"""
Setup GitHub secrets for Vercel CI/CD deployment
Run this script from the project root directory with proper credentials

Prerequisites:
  - GitHub CLI installed: brew install gh
  - GitHub CLI authenticated: gh auth login
  - Vercel projects created (frontend + backend)
  - VERCEL_TOKEN from https://vercel.com/account/tokens
  - VERCEL_ORG_ID from Vercel dashboard
  - VERCEL_PROJECT_ID_FRONTEND from Vercel frontend project
  - VERCEL_PROJECT_ID_BACKEND from Vercel backend project
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, Optional

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def run_command(cmd: list, capture_output: bool = False) -> tuple[bool, str]:
    """Run a shell command and return success status and output"""
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, check=False)
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.YELLOW}{'='*50}{Colors.NC}")
    print(f"{Colors.YELLOW}{text:^50}{Colors.NC}")
    print(f"{Colors.YELLOW}{'='*50}{Colors.NC}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.NC}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.NC}")

def check_prerequisites() -> bool:
    """Check if GitHub CLI is installed and authenticated"""
    print_header("Checking Prerequisites")
    
    # Check GitHub CLI
    success, _ = run_command(['gh', '--version'])
    if not success:
        print_error("GitHub CLI not installed")
        print_info("Install with: brew install gh")
        return False
    print_success("GitHub CLI installed")
    
    # Check GitHub authentication
    success, _ = run_command(['gh', 'auth', 'status'])
    if not success:
        print_error("GitHub CLI not authenticated")
        print_info("Authenticate with: gh auth login")
        return False
    print_success("GitHub CLI authenticated")
    
    # Check project root
    if not Path("package.json").exists() or not Path("frontend").exists() or not Path("backend").exists():
        print_error("Not in project root directory")
        print_info("Please run this script from the ShikkhaHub project root")
        return False
    print_success("Project root detected")
    
    return True

def get_repo_info() -> Optional[Dict[str, str]]:
    """Get repository owner and name from git config"""
    print_header("Getting Repository Information")
    
    success, output = run_command(['git', 'config', '--get', 'remote.origin.url'])
    if not success:
        print_error("Could not get git remote URL")
        return None
    
    # Parse git URL (both HTTPS and SSH formats)
    url = output.strip()
    if url.startswith('git@github.com:'):
        repo_part = url.replace('git@github.com:', '').replace('.git', '')
    elif url.startswith('https://github.com/'):
        repo_part = url.replace('https://github.com/', '').replace('.git', '')
    else:
        print_error(f"Invalid git URL format: {url}")
        return None
    
    owner, repo = repo_part.split('/')
    print_success(f"Repository: {owner}/{repo}")
    
    return {"owner": owner, "repo": repo}

def validate_secrets() -> Dict[str, str]:
    """Prompt user for and validate Vercel secrets"""
    print_header("Entering Vercel Credentials")
    
    secrets = {}
    
    # VERCEL_TOKEN
    print_info("Get VERCEL_TOKEN from: https://vercel.com/account/tokens")
    while True:
        token = input(f"{Colors.BLUE}Enter VERCEL_TOKEN: {Colors.NC}").strip()
        if len(token) > 20:  # Basic validation
            secrets['VERCEL_TOKEN'] = token
            print_success("VERCEL_TOKEN saved")
            break
        print_error("Invalid token length")
    
    # VERCEL_ORG_ID
    print_info("Get VERCEL_ORG_ID from your Vercel team settings")
    while True:
        org_id = input(f"{Colors.BLUE}Enter VERCEL_ORG_ID: {Colors.NC}").strip()
        if len(org_id) > 5:  # Basic validation
            secrets['VERCEL_ORG_ID'] = org_id
            print_success("VERCEL_ORG_ID saved")
            break
        print_error("Invalid org ID length")
    
    # VERCEL_PROJECT_ID_FRONTEND
    print_info("Get VERCEL_PROJECT_ID_FRONTEND from your frontend project in Vercel")
    while True:
        project_id = input(f"{Colors.BLUE}Enter VERCEL_PROJECT_ID_FRONTEND: {Colors.NC}").strip()
        if len(project_id) > 5:
            secrets['VERCEL_PROJECT_ID_FRONTEND'] = project_id
            print_success("VERCEL_PROJECT_ID_FRONTEND saved")
            break
        print_error("Invalid project ID length")
    
    # VERCEL_PROJECT_ID_BACKEND
    print_info("Get VERCEL_PROJECT_ID_BACKEND from your backend project in Vercel")
    while True:
        project_id = input(f"{Colors.BLUE}Enter VERCEL_PROJECT_ID_BACKEND: {Colors.NC}").strip()
        if len(project_id) > 5:
            secrets['VERCEL_PROJECT_ID_BACKEND'] = project_id
            print_success("VERCEL_PROJECT_ID_BACKEND saved")
            break
        print_error("Invalid project ID length")
    
    return secrets

def set_github_secret(owner: str, repo: str, secret_name: str, secret_value: str) -> bool:
    """Set a GitHub secret using gh CLI"""
    cmd = [
        'gh', 'secret', 'set',
        secret_name,
        '--repo', f"{owner}/{repo}",
        '--body', secret_value
    ]
    success, output = run_command(cmd)
    
    if success:
        print_success(f"GitHub secret '{secret_name}' set")
        return True
    else:
        print_error(f"Failed to set secret '{secret_name}': {output}")
        return False

def deploy_secrets(repo_info: Dict[str, str], secrets: Dict[str, str]) -> bool:
    """Deploy all secrets to GitHub"""
    print_header("Deploying GitHub Secrets")
    
    owner = repo_info['owner']
    repo = repo_info['repo']
    
    success_count = 0
    for secret_name, secret_value in secrets.items():
        if set_github_secret(owner, repo, secret_name, secret_value):
            success_count += 1
    
    if success_count == len(secrets):
        print_success(f"All {len(secrets)} secrets deployed successfully")
        return True
    else:
        print_error(f"Only {success_count}/{len(secrets)} secrets deployed")
        return False

def verify_secrets(owner: str, repo: str) -> bool:
    """Verify that all secrets were created"""
    print_header("Verifying Secrets")
    
    success, output = run_command([
        'gh', 'secret', 'list',
        '--repo', f"{owner}/{repo}"
    ])
    
    if not success:
        print_error("Could not list secrets")
        return False
    
    required_secrets = [
        'VERCEL_TOKEN',
        'VERCEL_ORG_ID',
        'VERCEL_PROJECT_ID_FRONTEND',
        'VERCEL_PROJECT_ID_BACKEND'
    ]
    
    lines = output.split('\n')
    created_secrets = set()
    
    for line in lines:
        for secret in required_secrets:
            if secret in line:
                created_secrets.add(secret)
                print_success(f"Secret '{secret}' found")
    
    if len(created_secrets) == len(required_secrets):
        return True
    else:
        missing = set(required_secrets) - created_secrets
        print_error(f"Missing secrets: {', '.join(missing)}")
        return False

def print_summary():
    """Print deployment summary"""
    print_header("Deployment Summary")
    
    print(f"""
{Colors.GREEN}✓ GitHub secrets configured successfully!{Colors.NC}

Next steps:
1. Verify CI/CD workflow is enabled in GitHub
2. Make a commit and push to {Colors.BLUE}dev{Colors.NC} branch
3. GitHub Actions should automatically trigger Vercel deployment
4. Check deployment status in:
   - GitHub: Actions tab
   - Vercel: Dashboard

To manually trigger deployment:
  git push origin dev

To view deployment logs:
  gh run list --repo owner/repo --workflow=vercel-deploy.yml

For more info see: docs/DEPLOYMENT.md
""")

def main():
    """Main execution flow"""
    print_header("ShikkhaHub GitHub Secrets Setup")
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites check failed")
        sys.exit(1)
    
    # Get repository information
    repo_info = get_repo_info()
    if not repo_info:
        print_error("Failed to get repository information")
        sys.exit(1)
    
    # Get credentials from user
    secrets = validate_secrets()
    
    # Deploy secrets
    if not deploy_secrets(repo_info, secrets):
        print_error("Failed to deploy secrets")
        sys.exit(1)
    
    # Verify secrets
    if not verify_secrets(repo_info['owner'], repo_info['repo']):
        print_error("Secret verification failed")
        sys.exit(1)
    
    # Print summary
    print_summary()
    print_success("GitHub secrets setup complete!")
    sys.exit(0)

if __name__ == "__main__":
    main()
