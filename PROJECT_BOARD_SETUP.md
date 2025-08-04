# GitHub Project Board Setup for LazySSH

This repository uses GitHub Actions to automatically manage a project board, but **GitHub Actions cannot create projects for personal accounts**. You need to create the project manually first.

## Step-by-Step Setup Instructions

### 1. Create the Project

1. Go to your GitHub projects page: https://github.com/users/Bochner/projects
2. Click **"New project"**
3. Choose **"Table"** view (this creates a Project V2)
4. Name it **"LazySSH Development"**
5. Click **"Create project"**

### 2. Set up the Status Field

The automation expects a "Status" field with specific options:

1. In your new project, click the **"+ Add field"** button
2. Choose **"Single select"** 
3. Name the field **"Status"**
4. Add these options (in order):
   - 📥 Triage
   - 📋 Backlog
   - 🔨 In Progress
   - 👀 Review/Testing
   - 🚀 Ready to Merge
   - ✅ Done
5. Save the field

### 3. Note the Project Number

After creating the project, look at the URL. It will be something like:
```
https://github.com/users/Bochner/projects/1
```

The number at the end (in this case `1`) is your project number.

### 4. Test the Automation

1. Go to the **Actions** tab in your repository
2. Click on **"Project Board Automation (v2)"**
3. Click **"Run workflow"**
4. Set the options:
   - `discover_projects`: **true** (to list your projects)
   - Leave other options as default
5. Click **"Run workflow"**

This will show you all available projects and their numbers.

### 5. Sync Existing Issues/PRs

Once you've confirmed the project exists:

1. Run the workflow again with:
   - `sync_all`: **true**
   - `project_number`: **your project number** (e.g., "1")
   - Leave other options as default

This will add all existing open issues and PRs to your project board.

## How the Automation Works

Once set up, the project board will automatically:

- **New Issues/PRs**: Added to "Backlog" (or "Triage" if labeled `needs-triage`)
- **Assigned Issues**: Moved to "In Progress"
- **PRs Ready for Review**: Moved to "Review/Testing"
- **Draft PRs**: Moved to "In Progress"
- **Closed Items**: Moved to "Done"
- **Approved PRs**: Moved to "Ready to Merge"
- **PRs with Changes Requested**: Moved back to "In Progress"

## Troubleshooting

### "Project not found" Error
- Run the workflow with `discover_projects: true` to see available projects
- Make sure you're using the correct project number
- Ensure the project is created as a "Project V2" (Table view)

### "Field not found" Error  
- Make sure you have a "Status" field (exact name)
- Ensure it's a "Single select" field
- Check that the options match the expected names

### Permission Errors
- The workflow uses `GITHUB_TOKEN` which should have the necessary permissions
- If you're in an organization, you might need additional permissions

## Manual Management

If automation isn't working, you can always manage the project board manually:
- Drag issues/PRs between columns
- Use the filters to find specific items
- Add custom fields as needed

The automation is designed to complement manual management, not replace it. 

testtest