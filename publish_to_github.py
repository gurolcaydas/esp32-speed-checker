#!/usr/bin/env python3
"""
Automated GitHub Publisher for ESP32 and similar projects.
Handles:
1. Credential protection via .gitignore
2. Git repository initialization & commit
3. Remote repository creation (via GitHub CLI `gh` or GitHub REST API token)
4. Push to branch 'main'
"""

import os
import sys
import shutil
import subprocess
import json
import urllib.request
import urllib.error

DEFAULT_GITIGNORE = """# Private configurations & credentials
config.json
stats.json
history.json
secrets.py
.env

# Firmware binaries
*.bin

# Python cache & IDE files
__pycache__/
*.py[cod]
.vscode/
.idea/
*.log
"""

def get_gh_executable():
    """Finds gh executable on PATH or in standard Windows installation paths."""
    # 1. On current PATH
    path = shutil.which("gh")
    if path:
        return f'"{path}"'

    # 2. Check standard Windows directories if terminal PATH hasn't refreshed yet
    standard_paths = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "GitHub CLI", "gh.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "GitHub CLI", "gh.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "GitHub CLI", "gh.exe"),
    ]
    for p in standard_paths:
        if os.path.isfile(p):
            return f'"{p}"'
    return None

def run_cmd(cmd, check=True):
    print(f"-> {cmd}")
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if res.stdout.strip():
        print(res.stdout.strip())
    if res.returncode != 0 and check:
        if res.stderr.strip():
            print(f"Error: {res.stderr.strip()}", file=sys.stderr)
        raise RuntimeError(f"Command failed: {cmd}")
    return res

def ensure_gitignore():
    if not os.path.exists(".gitignore"):
        print("Creating .gitignore to protect secrets & credentials...")
        with open(".gitignore", "w") as f:
            f.write(DEFAULT_GITIGNORE)
    else:
        with open(".gitignore", "r") as f:
            content = f.read()
        if "config.json" not in content:
            with open(".gitignore", "a") as f:
                f.write("\nconfig.json\nsecrets.py\n*.bin\n")

def create_repo_via_api(token, repo_name, description="", private=False):
    url = "https://api.github.com/user/repos"
    payload = json.dumps({
        "name": repo_name,
        "description": description,
        "private": private,
        "auto_init": False
    }).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "AutoGitPublisher-Script",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["clone_url"]
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        if "already exists" in err_body:
            print(f"Note: Repository '{repo_name}' already exists on GitHub.")
            user_res = run_cmd("git config user.name", check=False)
            user_name = user_res.stdout.strip()
            return f"https://github.com/{user_name}/{repo_name}.git"
        else:
            raise RuntimeError(f"GitHub API Error ({e.code}): {err_body}")

def main():
    folder_name = os.path.basename(os.path.abspath("."))
    repo_name = input(f"Enter repository name [{folder_name}]: ").strip() or folder_name
    visibility = input("Repository visibility (public/private) [public]: ").strip().lower() or "public"
    is_private = visibility == "private"

    ensure_gitignore()

    # Git init
    run_cmd("git init -b main", check=False)
    run_cmd("git branch -M main", check=False)

    # Ensure git user config exists
    res = run_cmd("git config user.name", check=False)
    if not res.stdout.strip():
        user_name = input("Git user.name not set. Enter your name or GitHub handle: ").strip()
        user_email = input("Git user.email not set. Enter your email: ").strip()
        if user_name:
            run_cmd(f'git config user.name "{user_name}"')
        if user_email:
            run_cmd(f'git config user.email "{user_email}"')

    # Stage and commit
    run_cmd("git add .")
    run_cmd('git commit -m "Initial commit"', check=False)

    # Check for GitHub CLI
    gh_bin = get_gh_executable()
    if gh_bin:
        # Check login status
        auth_check = run_cmd(f"{gh_bin} auth status", check=False)
        if auth_check.returncode != 0:
            print("\nGitHub CLI is installed but not logged in. Running web login...")
            subprocess.run(f"{gh_bin} auth login --web -p https", shell=True)

        vis_flag = "--private" if is_private else "--public"
        print(f"\nCreating and publishing repository '{repo_name}' via GitHub CLI...")
        res = run_cmd(f'{gh_bin} repo create "{repo_name}" {vis_flag} --source=. --remote=origin --push', check=False)
        if res.returncode == 0:
            print("\n==============================================")
            print(" SUCCESS! Project successfully published to GitHub.")
            print("==============================================\n")
            return
        elif "already exists" in res.stderr:
            print(f"Repository '{repo_name}' already exists on your GitHub account. Pushing code...")
            run_cmd("git push -u origin main", check=False)
            return

    # Fallback: GitHub Personal Access Token or existing Remote URL
    print("\nGitHub CLI fallback: You can use a GitHub Personal Access Token (PAT) or Repo URL.")
    choice = input("Enter (1) GitHub Token, or (2) Existing Repo URL, or (3) Exit [1]: ").strip() or "1"

    if choice == "1":
        token = input("Enter your GitHub Personal Access Token (with 'repo' scope): ").strip()
        if not token:
            print("No token provided. Aborting.")
            return
        clone_url = create_repo_via_api(token, repo_name, description=repo_name, private=is_private)
        auth_url = clone_url.replace("https://", f"https://{token}@")
        run_cmd("git remote remove origin", check=False)
        run_cmd(f'git remote add origin "{auth_url}"')
        run_cmd("git push -u origin main")
        run_cmd(f'git remote set-url origin "{clone_url}"')
        print(f"\nSUCCESS! Published to: {clone_url}")

    elif choice == "2":
        repo_url = input("Enter your GitHub repository clone URL: ").strip()
        run_cmd("git remote remove origin", check=False)
        run_cmd(f'git remote add origin "{repo_url}"')
        run_cmd("git push -u origin main")
        print(f"\nSUCCESS! Pushed to: {repo_url}")
    else:
        print("Publishing cancelled.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFailed: {e}", file=sys.stderr)
