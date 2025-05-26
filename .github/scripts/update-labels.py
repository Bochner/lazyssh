#!/usr/bin/env python3
"""
GitHub Label Color Update Script
Updates repository labels with vibrant, meaningful colors for better visibility and organization.
"""

import requests
import json
import os
import sys

# GitHub API configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = 'Bochner'
REPO_NAME = 'lazyssh'
API_BASE = 'https://api.github.com/repos'

# Vibrant color scheme for labels
LABEL_COLORS = {
    # Priority Labels - Red spectrum (urgent to low)
    'high-priority': 'D73A49',      # Bright red - urgent attention
    'medium-priority': 'FB8500',    # Orange - moderate attention  
    'low-priority': 'FFD60A',       # Yellow - can wait
    
    # Type Labels - Blue spectrum
    'bug': 'DC143C',                # Crimson - bugs need immediate attention
    'enhancement': '0366D6',        # GitHub blue - new features
    'epic': '6F42C1',               # Purple - large initiatives
    'documentation': '0075CA',      # Documentation blue
    'question': '7057FF',           # Light purple - questions
    
    # Component Labels - Green spectrum
    'scp-mode': '28A745',           # Green - core feature
    'connection-management': '22863A', # Dark green - infrastructure
    'ui-ux': '2EA043',              # Medium green - user interface
    'performance': '238636',        # Forest green - optimization
    'security': 'D1242F',           # Red - security is critical
    'testing': '17A2B8',            # Teal - testing/QA
    'quality-assurance': '20C997',  # Mint green - QA
    
    # Status Labels - Various colors
    'needs-triage': 'E99695',       # Light red - needs attention
    'in-progress': 'FBCA04',        # Yellow - work in progress
    'ready-for-review': '0E8A16',   # Green - ready for review
    'blocked': 'B60205',            # Dark red - blocked
    'duplicate': 'CFD3D7',          # Gray - duplicate
    'wontfix': 'FFFFFF',            # White - won't fix
    'invalid': 'E4E669',            # Light yellow - invalid
    'help-wanted': '008672',        # Teal - community help
    'good-first-issue': '7057FF',   # Purple - beginner friendly
    'keep-open': '0052CC',          # Blue - keep open
    'stale': 'FFEAA7',              # Light orange - stale
    
    # Infrastructure Labels - Tech colors
    'infrastructure': '5319E7',     # Purple - infrastructure
    'ci-cd': '1F77B4',              # Blue - CI/CD
    'dependencies': 'FF7F0E',       # Orange - dependencies
    'deployment': '2CA02C',         # Green - deployment
    'monitoring': 'D62728',         # Red - monitoring
    
    # Version Labels - Gradient
    'v1.0': '0052CC',               # Blue
    'v1.1': '0366D6',               # Lighter blue
    'v2.0': '6F42C1',               # Purple - major version
    'v2.1': '8B5CF6',               # Light purple
    'roadmap': 'F368E0',            # Pink - future planning
    
    # Special Labels
    'breaking-change': 'B60205',    # Dark red - breaking changes
    'feature-request': 'A2EEEF',    # Light blue - feature requests
    'refactor': 'FFEB3B',           # Bright yellow - refactoring
    'hotfix': 'FF5722',             # Orange-red - hotfixes
    'research': '9C27B0',           # Purple - research needed
}

def update_label_color(label_name, color):
    """Update a single label's color."""
    url = f"{API_BASE}/{REPO_OWNER}/{REPO_NAME}/labels/{label_name}"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    data = {
        'color': color
    }
    
    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print(f"✅ Updated '{label_name}' to #{color}")
        return True
    else:
        print(f"❌ Failed to update '{label_name}': {response.status_code} - {response.text}")
        return False

def create_label(label_name, color, description=""):
    """Create a new label if it doesn't exist."""
    url = f"{API_BASE}/{REPO_OWNER}/{REPO_NAME}/labels"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    data = {
        'name': label_name,
        'color': color,
        'description': description
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"✅ Created new label '{label_name}' with color #{color}")
        return True
    elif response.status_code == 422:
        # Label already exists, try to update it
        return update_label_color(label_name, color)
    else:
        print(f"❌ Failed to create '{label_name}': {response.status_code} - {response.text}")
        return False

def get_existing_labels():
    """Get all existing labels in the repository."""
    url = f"{API_BASE}/{REPO_OWNER}/{REPO_NAME}/labels"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return {label['name']: label for label in response.json()}
    else:
        print(f"❌ Failed to get existing labels: {response.status_code}")
        return {}

def main():
    """Main function to update all label colors."""
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    print(f"🎨 Updating label colors for {REPO_OWNER}/{REPO_NAME}")
    print("=" * 50)
    
    # Get existing labels
    existing_labels = get_existing_labels()
    print(f"📋 Found {len(existing_labels)} existing labels")
    
    success_count = 0
    total_count = len(LABEL_COLORS)
    
    # Update or create each label
    for label_name, color in LABEL_COLORS.items():
        if label_name in existing_labels:
            if update_label_color(label_name, color):
                success_count += 1
        else:
            # Create new label with appropriate description
            descriptions = {
                'high-priority': 'Critical issues requiring immediate attention',
                'medium-priority': 'Important issues with moderate urgency',
                'low-priority': 'Nice-to-have improvements and minor issues',
                'bug': 'Something isn\'t working correctly',
                'enhancement': 'New feature or improvement request',
                'epic': 'Large feature or initiative spanning multiple issues',
                'documentation': 'Improvements or additions to documentation',
                'question': 'Further information is requested',
                'scp-mode': 'Related to SCP file transfer functionality',
                'connection-management': 'SSH connection handling and management',
                'ui-ux': 'User interface and experience improvements',
                'performance': 'Performance optimization and improvements',
                'security': 'Security-related issues and improvements',
                'testing': 'Testing infrastructure and test cases',
                'quality-assurance': 'Quality assurance and code review',
                'needs-triage': 'New issue requiring initial review and labeling',
                'in-progress': 'Currently being worked on',
                'ready-for-review': 'Ready for code review',
                'blocked': 'Blocked by external dependencies or issues',
                'duplicate': 'This issue or pull request already exists',
                'wontfix': 'This will not be worked on',
                'invalid': 'This doesn\'t seem right',
                'help-wanted': 'Extra attention is needed',
                'good-first-issue': 'Good for newcomers',
                'keep-open': 'Prevent automatic closure',
                'stale': 'No recent activity',
                'infrastructure': 'Development infrastructure and tooling',
                'ci-cd': 'Continuous integration and deployment',
                'dependencies': 'External dependencies and package management',
                'deployment': 'Deployment and release processes',
                'monitoring': 'Monitoring and observability',
                'v1.0': 'Version 1.0 milestone',
                'v1.1': 'Version 1.1 milestone',
                'v2.0': 'Version 2.0 major release',
                'v2.1': 'Version 2.1 milestone',
                'roadmap': 'Future planning and roadmap items',
                'breaking-change': 'Changes that break backward compatibility',
                'feature-request': 'Request for new functionality',
                'refactor': 'Code refactoring and cleanup',
                'hotfix': 'Critical fix requiring immediate release',
                'research': 'Research and investigation needed',
            }
            
            description = descriptions.get(label_name, "")
            if create_label(label_name, color, description):
                success_count += 1
    
    print("=" * 50)
    print(f"🎉 Successfully updated {success_count}/{total_count} labels")
    
    if success_count == total_count:
        print("✅ All labels updated successfully!")
    else:
        print(f"⚠️  {total_count - success_count} labels failed to update")

if __name__ == "__main__":
    main() 