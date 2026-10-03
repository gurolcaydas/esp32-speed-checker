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
        # Verify config.json is ignored
        with open(".gitignore", "r") as f:
            content = f.read()
        if "config.json" not in content:
            with open(".gitignore", "a") as f:
                f.write("\nconfig.json\nsecrets.py\n*.bin\n")

def check_gh_installed():
    res = run_cmd("gh --version", check=False)
    return res.returncode == 0

def check_gh_logged_in():
    res = run_cmd("gh auth status", check=False)
    return res.returncode == 0

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
    run_cmd('git commit -m "Initial commit: ESP32 Network Speed Checker & Diagnostic Station"', check=False)

    # Check for GitHub CLI
    if check_gh_installed():
        if not check_gh_logged_in():
            print("\nGitHub CLI is installed but not authenticated.")
            print("Running 'gh auth login'...")
            subprocess.run("gh auth login", shell=True)

        vis_flag = "--private" if is_private else "--public"
        print(f"\nCreating and publishing repository '{repo_name}' via GitHub CLI...")
        res = run_cmd(f'gh repo create "{repo_name}" {vis_flag} --source=. --remote=origin --push', check=False)
        if res.returncode == 0:
            print("\nSUCCESS! Repository published to GitHub.")
            return

    # Fallback: GitHub Personal Access Token or existing Remote URL
    print("\nGitHub CLI not found or not used. You can use a GitHub Personal Access Token (PAT) or Repo URL.")
    choice = input("Enter (1) GitHub Token, or (2) Existing Repo URL, or (3) Exit [1]: ").strip() or "1"

    if choice == "1":
        token = input("Enter your GitHub Personal Access Token (with 'repo' scope): ").strip()
        if not token:
            print("No token provided. Aborting.")
            return
        clone_url = create_repo_via_api(token, repo_name, description="ESP32 Network Speed Checker & Diagnostics", private=is_private)
        # Push with token
        auth_url = clone_url.replace("https://", f"https://{token}@")
        run_cmd("git remote remove origin", check=False)
        run_cmd(f'git remote add origin "{auth_url}"')
        run_cmd("git push -u origin main")
        # Sanitize remote URL after push so token is not stored in plaintext .git/config
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
