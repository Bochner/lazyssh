# GitHub Project Board Setup Guide

Since GitHub's API has limitations for creating projects on personal accounts, you'll need to set up the project board manually. Follow these steps:

## Step 1: Create the Project

1. Go to your GitHub profile: https://github.com/users/YOUR_USERNAME/projects
2. Click the green "New project" button
3. Choose "Table" view (recommended) or "Board" view
4. Set the project name to: **LazySSH Development**
5. Add a description (optional): "Issue and PR tracking for LazySSH development"
6. Click "Create project"

## Step 2: Configure the Status Field

1. In your new project, click "⚙️" (settings) in the top right
2. Look for "Fields" section and find the "Status" field (should exist by default)
3. Edit the Status field to have these exact options:
   - 📥 Triage
   - 📋 Backlog
   - 🔨 In Progress
   - 👀 Review/Testing
   - 🚀 Ready to Merge
   - ✅ Done

## Step 3: Get Your Project Number

1. In your project, look at the URL: `https://github.com/users/YOUR_USERNAME/projects/X`
2. The `X` at the end is your project number (usually 1 for your first project)
3. Remember this number - you'll need it for the workflow

## Step 4: Link Repository to Project

1. In your project, click "Add items" 
2. Search for and select your repository: `YOUR_USERNAME/lazyssh`
3. This creates the connection between your repo and project

## Step 5: Test the Automation

1. Go to your repository: https://github.com/YOUR_USERNAME/lazyssh
2. Navigate to "Actions" tab
3. Click on "Project Board Automation (v2)"
4. Click "Run workflow"
5. If your project number is not 1, enter it in the "Project number" field
6. Check "Sync all open issues and PRs to project board"
7. Click "Run workflow"

## Troubleshooting

### Workflow Still Failing?

If you're still getting errors:

1. **Check Project Number**: Make sure you're using the correct project number from the URL
2. **Check Project Name**: The workflow expects "LazySSH Development" - make sure the name matches exactly
3. **Check Field Name**: The Status field must be named "Status" (case-sensitive)
4. **Permissions**: Make sure the repository has access to your project

### Manual Workflow Run

You can also run the workflow for specific issues or PRs:

1. Go to Actions → Project Board Automation (v2)
2. Click "Run workflow"
3. Enter specific issue or PR number in the respective field
4. Enter your project number if it's not 1
5. Click "Run workflow"

### View Workflow Logs

If something isn't working:

1. Go to Actions → Project Board Automation (v2)
2. Click on the latest run
3. Expand the job steps to see detailed logs
4. Look for any error messages or helpful output

The workflow will now gracefully handle missing projects and provide helpful error messages instead of failing completely. 