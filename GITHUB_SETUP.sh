# GitHub Setup — One Time Only
# Run this ONCE on your machine. After this, push.bat works forever.

# OPTION 1 — GitHub CLI (easiest, recommended)
# Install from: https://cli.github.com
# Then run:
gh auth login
# Follow the prompts. Choose HTTPS. It saves your credentials securely.
# After this: git push works from any terminal on your machine.

# OPTION 2 — Windows Credential Manager (built into Windows)
# Run this once in PowerShell:
git config --global credential.helper manager
# Next time you push, Windows will ask for your GitHub username + token.
# It saves it securely. Never asks again.

# OPTION 3 — Store token in git config (less secure but simple)
# Replace YOUR_TOKEN with a Personal Access Token from:
# github.com -> Settings -> Developer Settings -> Personal Access Tokens
git remote set-url origin https://YOUR_TOKEN@github.com/huey-san3/Producer-san3.git

# After any of these options: just double-click push.bat to push changes.
# No tokens in chat. No credentials shared anywhere.
