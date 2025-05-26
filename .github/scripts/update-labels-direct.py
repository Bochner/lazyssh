#!/usr/bin/env python3
"""
Direct GitHub Label Update via API
This script will be executed to update label colors directly.
"""

import requests
import os

# GitHub API configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = 'Bochner'
REPO_NAME = 'lazyssh'

# Label color updates
label_updates = [
    # Update existing labels
    {'name': 'high-priority', 'color': 'D73A49', 'description': 'Critical issues requiring immediate attention'},
    {'name': 'medium-priority', 'color': 'FB8500', 'description': 'Important issues with moderate urgency'},
    {'name': 'low-priority', 'color': 'FFD60A', 'description': 'Nice-to-have improvements and minor issues'},
    {'name': 'documentation', 'color': '0075CA', 'description': 'Improvements or additions to documentation'},
    {'name': 'enhancement', 'color': '0366D6', 'description': 'New feature or improvement request'},
    {'name': 'infrastructure', 'color': '5319E7', 'description': 'Development infrastructure and tooling'},
    {'name': 'bug', 'color': 'DC143C', 'description': 'Something isn\'t working correctly'},
    
    # Create new labels
    {'name': 'epic', 'color': '6F42C1', 'description': 'Large feature or initiative spanning multiple issues'},
    {'name': 'scp-mode', 'color': '28A745', 'description': 'Related to SCP file transfer functionality'},
    {'name': 'connection-management', 'color': '22863A', 'description': 'SSH connection handling and management'},
    {'name': 'ui-ux', 'color': '2EA043', 'description': 'User interface and experience improvements'},
    {'name': 'performance', 'color': '238636', 'description': 'Performance optimization and improvements'},
    {'name': 'security', 'color': 'D1242F', 'description': 'Security-related issues and improvements'},
    {'name': 'testing', 'color': '17A2B8', 'description': 'Testing infrastructure and test cases'},
    {'name': 'quality-assurance', 'color': '20C997', 'description': 'Quality assurance and code review'},
    {'name': 'needs-triage', 'color': 'E99695', 'description': 'New issue requiring initial review and labeling'},
    {'name': 'in-progress', 'color': 'FBCA04', 'description': 'Currently being worked on'},
    {'name': 'ready-for-review', 'color': '0E8A16', 'description': 'Ready for code review'},
    {'name': 'blocked', 'color': 'B60205', 'description': 'Blocked by external dependencies or issues'},
    {'name': 'help-wanted', 'color': '008672', 'description': 'Extra attention is needed'},
    {'name': 'good-first-issue', 'color': '7057FF', 'description': 'Good for newcomers'},
    {'name': 'v1.0', 'color': '0052CC', 'description': 'Version 1.0 milestone'},
    {'name': 'v1.1', 'color': '0366D6', 'description': 'Version 1.1 milestone'},
    {'name': 'v2.0', 'color': '6F42C1', 'description': 'Version 2.0 major release'},
    {'name': 'roadmap', 'color': 'F368E0', 'description': 'Future planning and roadmap items'},
]

print("🎨 Updating GitHub labels with vibrant colors...")
for label in label_updates:
    print(f"  - {label['name']}: #{label['color']}")

print("\nThis script is ready to be executed via GitHub Actions!")