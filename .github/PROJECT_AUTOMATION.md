# LazySSH Project Management Automation

> **🚀 UPDATED**: This workflow has been migrated from the deprecated GitHub Projects Classic API to the new **GitHub Projects v2 API** using GraphQL.

## 🚀 Projects v2 Migration

### What's New

- **Projects v2 Support**: Uses the modern GitHub Projects API with GraphQL
- **Better Performance**: More efficient queries and operations
- **Enhanced Features**: Support for custom fields and better status management
- **Fixed Issues**: Resolved the boolean default value linting error

### Prerequisites for Projects v2

#### 1. Create a GitHub Project v2

Since the workflow now uses Projects v2, you need to create a new project:

1. Go to your GitHub profile or organization
2. Click on **Projects** tab
3. Click **New project**
4. Choose **Board** layout
5. Name it "LazySSH Development" (or update `PROJECT_NAME` in the workflow)

#### 2. Add Status Field

The workflow expects a **Status** field with these options:
- 📥 Triage
- 📋 Backlog  
- 🔨 In Progress
- 👀 Review/Testing
- 🚀 Ready to Merge
- ✅ Done

You can create this manually or run the workflow with `workflow_dispatch` to auto-create it.

### Migration from Projects Classic

If you're migrating from the old workflow:

1. **Create a new Project v2** (Projects Classic is deprecated)
2. **Set up the Status field** as described above
3. **Run sync workflow** to import existing issues/PRs
4. **Archive old Project Classic board** once migration is complete

### Limitations

- Projects v2 API is different from Classic - cards become "items" with field values
- Maximum 100 items per query (pagination needed for larger projects)
- GraphQL queries are more complex but more powerful

## 🚀 Features Implemented

### 1. Auto-Assignment Workflows
**File**: `.github/workflows/auto-assignment.yml`

Automatically assigns issues and pull requests based on:
- **Content Analysis**: Keywords in title/body (e.g., "scp", "security", "performance")
- **File Changes**: Assigns based on which files are modified in PRs
- **Priority**: High-priority and critical items get immediate assignment
- **Component Areas**: Specific LazySSH modules trigger relevant assignments

**Triggers**: New issues and PRs

### 2. Label Synchronization
**File**: `.github/workflows/label-sync.yml`

Maintains consistent labeling across the repository:
- **Standard Labels**: Comprehensive set of priority, type, and component labels
- **LazySSH-Specific**: Labels for SCP mode, tunnel management, SSH connections
- **Workflow Labels**: Triage, testing, review status
- **Platform Labels**: Linux, macOS, Windows-specific issues
- **Audit Reports**: Weekly analysis of label usage and recommendations

**Triggers**: Weekly schedule, manual dispatch, label file changes

### 3. Milestone Automation
**File**: `.github/workflows/milestone-automation.yml`

Intelligent milestone management:
- **Auto-Assignment**: Issues assigned to milestones based on labels and priority
- **Version Planning**: Automatic creation of patch, minor, and major release milestones
- **Progress Tracking**: Weekly reports on milestone completion
- **Smart Logic**: Critical issues → patch releases, features → minor releases

**Triggers**: Issue/PR events, weekly schedule, manual dispatch

### 4. Project Board Automation (Projects v2)
**File**: `.github/workflows/project-board-automation.yml`

GitHub Project Board management using the modern Projects v2 API:
- **Automatic Movement**: Items move between status columns based on events
- **GraphQL Integration**: Uses GitHub's GraphQL API for better performance
- **Status Field Management**: Creates and manages custom Status fields
- **Review Integration**: PR reviews trigger board movements
- **Manual Actions**: Support for manual workflow dispatch with options

**Status Column Structure**:
- 📥 Triage
- 📋 Backlog  
- 🔨 In Progress
- 👀 Review/Testing
- 🚀 Ready to Merge
- ✅ Done

**Automatic Triggers**:

#### Issues
- **Opened**: Adds to Triage (if has `needs-triage` label) or Backlog
- **Closed**: Moves to Done
- **Reopened**: Moves to Backlog
- **Labeled**: 
  - `work-in-progress` → In Progress
  - `ready-for-review` → Review/Testing
  - `needs-triage` → Triage
- **Assigned**: Moves to In Progress

#### Pull Requests
- **Opened**: Adds to Backlog or Review/Testing (if `ready-for-review` label)
- **Closed**: Moves to Done
- **Reopened**: Moves to Review/Testing
- **Ready for Review**: Moves to Review/Testing
- **Converted to Draft**: Moves to In Progress

#### PR Reviews
- **Approved**: Moves to Ready to Merge (if no change requests)
- **Changes Requested**: Moves to In Progress

**Manual Actions**:
```yaml
# Sync all open issues/PRs to project
sync_all: true

# Process specific items
issue_number: "123"
pr_number: "456"

# Use specific project number
project_number: "1"
```

**Configuration**:
- Project Name: "LazySSH Development" (configurable via `PROJECT_NAME` env var)
- Automatic project detection by repository owner
- Smart status field mapping using keyword detection

### 5. Branch Protection Enforcement
**File**: `.github/workflows/branch-protection.yml`

Security and quality enforcement:
- **Protection Rules**: Requires PR reviews, status checks
- **Compliance Monitoring**: Checks for violations in merged PRs
- **Security Audit**: Repository settings and security feature verification
- **Automated Reports**: Weekly compliance and security status

**Protection Features**:
- Required PR reviews (1 approval minimum)
- Required status checks for CI/tests/linting
- No force pushes to main
- Stale review dismissal

## 🏷️ Labels System

### Priority Labels
- `critical` - Issues needing immediate attention
- `high-priority` - High priority issues  
- `medium-priority` - Medium priority issues
- `low-priority` - Low priority issues

### Type Labels
- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation improvements
- `question` - Further information requested

### LazySSH Component Labels
- `scp-mode` - SCP file transfer functionality
- `tunnel-management` - SSH tunnel management
- `connection-handling` - SSH connection handling
- `ui-ux` - User interface improvements
- `performance` - Performance optimizations
- `security` - Security-related issues
- `configuration` - Settings and configuration

### Workflow Labels
- `needs-triage` - Requires review and categorization
- `needs-reproduction` - Bug needs reproduction steps
- `needs-testing` - Requires testing before merge
- `ready-for-review` - Ready for code review
- `work-in-progress` - Currently being worked on
- `blocked` - Blocked by dependencies

### Special Labels
- `good-first-issue` - Good for newcomers
- `help-wanted` - Community contributions welcome
- `stale` - Inactive items (auto-applied)
- `keep-open` - Exempt from stale bot

## 🔄 Automation Triggers

### Real-time Triggers
- **Issue opened** → Auto-label, assign, add to project board
- **PR opened** → Auto-assign reviewers, add to board, milestone assignment
- **PR ready for review** → Move to review column
- **Issue/PR closed** → Move to done column
- **Labels added** → Trigger milestone assignment, board movement

### Scheduled Triggers
- **Monday 2 AM UTC** → Label sync and audit
- **Monday 5 AM UTC** → Branch protection enforcement
- **Monday 6 AM UTC** → Milestone progress reports
- **Monday 9 AM UTC** → Project metrics and stale issue management

## 🛠️ Setup and Configuration

### Initial Setup
1. **Run label sync**: Manually trigger the label sync workflow
2. **Create project board**: Run project board creation workflow
3. **Enable branch protection**: Ensure main branch protection is active
4. **Configure milestones**: Let milestone automation create initial milestones

### Customization
To customize the automation for your needs:

1. **Auto-assignment logic**: Edit assignment criteria in `auto-assignment.yml`
2. **Label definitions**: Modify label set in `label-sync.yml`
3. **Milestone rules**: Adjust milestone assignment logic in `milestone-automation.yml`
4. **Project board columns**: Change column names/logic in `project-board-automation.yml`
5. **Branch protection**: Update protection rules in `branch-protection.yml`

### Manual Triggers
All workflows support manual triggering via GitHub Actions UI:
- Go to Actions tab
- Select workflow
- Click "Run workflow"

## 📊 Metrics and Reporting

### Weekly Reports Generated
- **Project metrics**: Open issues, PRs, priority breakdown
- **Milestone progress**: Completion percentages, overdue milestones
- **Label usage**: Most used labels, unlabeled items
- **Branch protection**: Compliance violations, security status

### Key Performance Indicators
- Issue triage time (via `needs-triage` label)
- PR review time (board column duration)
- Milestone completion rates
- Security compliance score

## 🔒 Security Features

### CODEOWNERS Integration
**File**: `.github/CODEOWNERS`
- Automatic reviewer assignment for code changes
- Ensures security-critical files get proper review
- Maintains code quality standards

### Security Policy
**File**: `.github/SECURITY.md`
- Vulnerability reporting procedures
- Security best practices
- Supported versions matrix

### Branch Protection
- Prevents direct pushes to main
- Requires code review for all changes
- Enforces status checks (tests, linting)
- Monitors compliance violations

## 🎯 Best Practices

### For Contributors
1. **Use descriptive titles**: Include component names and issue types
2. **Add relevant labels**: Help automation categorize correctly
3. **Follow PR template**: Ensure proper review assignment
4. **Keep issues focused**: One issue per problem/feature

### For Maintainers
1. **Regular triage**: Review `needs-triage` labeled items weekly
2. **Milestone management**: Keep milestones current and achievable
3. **Label hygiene**: Use automation reports to maintain label quality
4. **Security monitoring**: Review weekly security compliance reports

## 🔧 Troubleshooting

### Common Issues
1. **Automation not triggering**: Check workflow permissions and triggers
2. **Labels not syncing**: Verify repository admin permissions
3. **Project board not updating**: Ensure project board exists and is accessible
4. **Milestones not creating**: Check for duplicate names and permissions

### Projects v2 Specific Issues

1. **"Project not found"**
   - Ensure project number is correct
   - Check project is owned by repository owner
   - Verify project is public/accessible

2. **"No Status field found"**
   - Create a Status field manually
   - Ensure field name contains "status", "column", or "state"

3. **"Permission denied"**
   - Check `GITHUB_TOKEN` permissions
   - For org repos, ensure workflow has project access

### Debug Steps for Projects v2
1. Check workflow logs in Actions tab
2. Verify project number and ownership
3. Confirm Status field exists and has proper options
4. Test with manual workflow dispatch first

### Debug Information
- All workflows log detailed information to Actions console
- Check individual job outputs for specific error messages
- Verify GitHub token permissions for repository operations

## 🧪 Testing Projects v2 Automation

To test the workflow:

1. **Create a test issue** with `needs-triage` label
2. **Assign the issue** to someone
3. **Add `work-in-progress` label**
4. **Close the issue**

Each action should move the item through the appropriate status columns.

## 📚 API References

- [GitHub Projects v2 API](https://docs.github.com/en/graphql/reference/objects#projectv2)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)
- [GitHub Actions github-script](https://github.com/actions/github-script)

## 🔄 Projects v2 Migration Checklist

- [ ] Create new GitHub Project v2
- [ ] Set up Status field with proper options
- [ ] Update workflow file (already done)
- [ ] Test with sample issue/PR
- [ ] Run sync workflow for existing items
- [ ] Archive old Projects Classic board
- [ ] Update documentation references 

## 📈 Future Enhancements

Potential improvements to consider:
- Integration with external project management tools
- Slack/Discord notifications for important events
- Advanced analytics and dashboard creation
- Machine learning-based label prediction
- Integration with CI/CD pipelines for deployment automation

---

For questions or issues with the automation setup, please create an issue with the `automation` label. 