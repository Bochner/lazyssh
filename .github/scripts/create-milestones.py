#!/usr/bin/env python3
"""
GitHub Milestone Creation Script
Creates development milestones for LazySSH project management.
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta

# GitHub API configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = 'Bochner'
REPO_NAME = 'lazyssh'
API_BASE = 'https://api.github.com/repos'

# Milestone definitions
MILESTONES = [
    {
        'title': 'LazySSH v1.1 - Performance & Stability',
        'description': '''Performance improvements and stability enhancements for the current release.

**Key Goals:**
- Optimize SCP command performance (#51)
- Implement transfer reliability (#43)
- Enhance error handling and recovery
- Improve connection management

**Success Criteria:**
- 70% reduction in command execution overhead
- Robust error handling for all failure scenarios
- Comprehensive test coverage for core features
- Zero critical bugs in production''',
        'due_on': (datetime.now() + timedelta(days=45)).isoformat(),  # 6 weeks
        'state': 'open'
    },
    {
        'title': 'LazySSH v2.0 - Major Release',
        'description': '''Major release with modernized architecture and enhanced user experience.

**Key Goals:**
- Complete SCP mode modernization (#53)
- Rich live display implementation (#45)
- Batch file operations (#44)
- SSH key management (#37)
- Plugin system foundation

**Success Criteria:**
- Modern, maintainable codebase architecture
- Intuitive user interface with real-time feedback
- Comprehensive documentation and examples
- Community-ready contribution guidelines
- Performance benchmarks and optimization''',
        'due_on': (datetime.now() + timedelta(days=90)).isoformat(),  # 3 months
        'state': 'open'
    },
    {
        'title': 'Testing & Quality Assurance',
        'description': '''Comprehensive testing infrastructure and quality assurance implementation.

**Key Goals:**
- Unit test suite with 90%+ coverage
- Integration test framework
- Performance benchmarking
- Security testing automation
- CI/CD pipeline enhancements

**Success Criteria:**
- Automated test execution on all PRs
- Performance regression detection
- Security vulnerability scanning
- Cross-platform testing validation
- Quality gates for releases''',
        'due_on': (datetime.now() + timedelta(days=60)).isoformat(),  # 8 weeks
        'state': 'open'
    },
    {
        'title': 'Documentation & Community',
        'description': '''Complete documentation overhaul and community engagement features.

**Key Goals:**
- Comprehensive user guide and tutorials
- API documentation and examples
- Architecture and development guides
- Video tutorials and demos
- Community contribution tools

**Success Criteria:**
- Complete documentation for all features
- Interactive examples and demos
- Clear contribution guidelines
- Onboarding materials for new users
- Community feedback integration''',
        'due_on': (datetime.now() + timedelta(days=75)).isoformat(),  # 10 weeks
        'state': 'open'
    },
    {
        'title': 'Future Enhancements',
        'description': '''Long-term enhancements and experimental features.

**Key Goals:**
- Advanced SSH features and protocols
- Multi-server management capabilities
- Advanced monitoring and analytics
- Plugin ecosystem development
- Enterprise features and integrations

**Success Criteria:**
- Research and prototyping complete
- Community feedback incorporated
- Technical feasibility validated
- Roadmap for implementation defined''',
        'due_on': (datetime.now() + timedelta(days=180)).isoformat(),  # 6 months
        'state': 'open'
    }
]

def create_milestone(milestone_data):
    """Create a single milestone."""
    url = f"{API_BASE}/{REPO_OWNER}/{REPO_NAME}/milestones"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers, json=milestone_data)
    
    if response.status_code == 201:
        milestone = response.json()
        print(f"✅ Created milestone '{milestone['title']}'")
        print(f"   📅 Due: {milestone.get('due_on', 'No due date')}")
        print(f"   🔗 URL: {milestone['html_url']}")
        return True
    elif response.status_code == 422:
        error_data = response.json()
        if 'already_exists' in str(error_data):
            print(f"⚠️  Milestone '{milestone_data['title']}' already exists")
            return True
        else:
            print(f"❌ Failed to create '{milestone_data['title']}': {error_data}")
            return False
    else:
        print(f"❌ Failed to create '{milestone_data['title']}': {response.status_code} - {response.text}")
        return False

def get_existing_milestones():
    """Get all existing milestones."""
    url = f"{API_BASE}/{REPO_OWNER}/{REPO_NAME}/milestones"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return {milestone['title']: milestone for milestone in response.json()}
    else:
        print(f"❌ Failed to get existing milestones: {response.status_code}")
        return {}

def main():
    """Main function to create all milestones."""
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    
    print(f"🎯 Creating milestones for {REPO_OWNER}/{REPO_NAME}")
    print("=" * 60)
    
    # Get existing milestones
    existing_milestones = get_existing_milestones()
    print(f"📋 Found {len(existing_milestones)} existing milestones")
    
    success_count = 0
    total_count = len(MILESTONES)
    
    # Create each milestone
    for milestone_data in MILESTONES:
        if milestone_data['title'] not in existing_milestones:
            if create_milestone(milestone_data):
                success_count += 1
        else:
            print(f"⚠️  Milestone '{milestone_data['title']}' already exists")
            success_count += 1
        print()  # Add spacing between milestones
    
    print("=" * 60)
    print(f"🎉 Successfully processed {success_count}/{total_count} milestones")
    
    if success_count == total_count:
        print("✅ All milestones created or verified!")
        print("\n📋 Next Steps:")
        print("1. Review milestone descriptions and due dates")
        print("2. Assign existing issues to appropriate milestones")
        print("3. Use milestones for sprint planning and progress tracking")
        print("4. Update milestone progress regularly")
    else:
        print(f"⚠️  {total_count - success_count} milestones failed to create")

if __name__ == "__main__":
    main() 