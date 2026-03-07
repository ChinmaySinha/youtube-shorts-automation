"""
GitHub Secrets Setup Helper

Run this script LOCALLY to generate base64-encoded secrets
that you need to paste into your GitHub repository settings.

Usage:
    python setup_github_secrets.py

It will output the base64 values for:
1. YOUTUBE_TOKEN_B64 (from token.pickle)
2. CLIENT_SECRETS_B64 (from client_secrets.json)
3. DOTENV_B64 (from .env)

You then paste these values into:
GitHub repo > Settings > Secrets and Variables > Actions > New repository secret
"""

import base64
import os
import sys

def encode_file(filepath: str) -> str:
    """Read a file and return its base64-encoded content."""
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def main():
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_agent_system")
    
    files = {
        "YOUTUBE_TOKEN_B64": os.path.join(base_dir, "token.pickle"),
        "CLIENT_SECRETS_B64": os.path.join(base_dir, "client_secrets.json"),
        "DOTENV_B64": os.path.join(base_dir, ".env"),
    }
    
    print("=" * 60)
    print("  GitHub Secrets Setup")
    print("=" * 60)
    print()
    print("Go to: GitHub repo > Settings > Secrets and Variables > Actions")
    print("Click 'New repository secret' for each of the following:")
    print()
    
    for secret_name, filepath in files.items():
        if os.path.exists(filepath):
            encoded = encode_file(filepath)
            print(f"--- Secret: {secret_name} ---")
            print(f"File: {filepath}")
            print(f"Size: {len(encoded)} chars")
            print(f"Value (first 50 chars): {encoded[:50]}...")
            
            # Save to a temp file for easy copy-paste
            output_file = os.path.join(base_dir, f"_secret_{secret_name}.txt")
            with open(output_file, 'w') as f:
                f.write(encoded)
            print(f"SAVED TO: {output_file}")
            print(f"  -> Open this file and copy the ENTIRE content as the secret value")
            print()
        else:
            print(f"[MISSING] {secret_name}: File not found at {filepath}")
            print()
    
    # Also remind about API keys
    print("=" * 60)
    print("  ALSO ADD THESE SECRETS (plain text, from your .env file):")
    print("=" * 60)
    print()
    
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key = line.split('=', 1)[0].strip()
                    print(f"  Secret name: {key}")
    
    print()
    print("You also need: PEXELS_API_KEY (if you have one)")
    print()
    print("Done! After adding all secrets, push your code and the")
    print("workflow will run automatically at the scheduled times.")
    print("You can also trigger it manually from the Actions tab.")


if __name__ == '__main__':
    main()
