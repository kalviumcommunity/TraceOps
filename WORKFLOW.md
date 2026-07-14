# TraceOps Team Workflow Documentation

This document outlines the standard branching, commit messaging, and code review workflows for the TraceOps engineering team.

## Branching Strategy

Our team uses a feature-branching workflow to ensure the `main` branch remains clean, stable, and always ready for production deployment.

### Branch Guidelines
1. **Main Branch (`main`)**: Holds stable, fully-tested, and deployable code. Direct commits to `main` are strictly prohibited.
2. **Feature Branches (`feature/[description]`)**: All new development, feature additions, and sprint tasks are developed on isolated feature branches. Example: `feature/github-workflow-setup` or `feature/data-ingestion`.
3. **Hotfix Branches (`fix/[description]`)**: Emergency bug fixes are created on dedicated fix branches. Example: `fix/db-zero-division`.
4. **Branch Lifecycle**: Feature branches are deleted immediately after their corresponding Pull Request is approved and merged into `main`.

## Commit Message Convention

Our team follows the Conventional Commits specification. This ensures that the repository history remains semantic and readable for developers and automation tools.

### Format
```text
[type]: [description]

[optional body explaining why]
```

### Types Used
- **`feat`**: A new feature or analytical capability added to the codebase.
- **`fix`**: A bug fix or correction in the logic.
- **`docs`**: Documentation changes only (e.g., updates to README or markdown guides).
- **`refactor`**: Code restructuring that neither fixes a bug nor adds a feature.
- **`test`**: Adding new tests or modifying existing tests.
- **`chore`**: Maintenance tasks, library upgrades, or configuration tweaks.

### Why It Matters
Using a standardized commit structure allows us to track features/fixes accurately, generate changelogs automatically, and understand the history of any code changes at a glance.

---

## Pull Request & Code Review Process

Pull Requests (PRs) serve as a quality gate to prevent untested, buggy, or undocumented changes from reaching the `main` branch.

### Code Review Guidelines
1. **Mandatory Approvals**: A PR must receive at least one approval from a teammate before it can be merged.
2. **Review Focus Areas**:
   - **Correctness & Clarity**: Is the code logical, well-structured, and easy to read?
   - **Data Integrity**: Does the change protect transactional schemas and prevent data loss/corruption?
   - **Test Coverage**: Are validation scripts or unit tests included and passing?
   - **Commit Quality**: Do commit messages follow the team convention?
3. **Merging**: Once approved, the author should squash and merge the PR into `main` and delete the feature branch.

---

## GitHub Issue Tracking Approach

All project work is managed and tracked transparently through GitHub Issues.

### Issue Lifecycle
1. **Issue Creation**: No code should be written without a corresponding GitHub Issue detailing the problem or goal.
2. **Formatting**: Every issue must have:
   - A clear, action-oriented title.
   - A description detailing context, scope, and acceptance criteria.
   - At least one categorization label (`feature`, `bug`, `documentation`, `data-pipeline`).
   - One clear assignee who is responsible for the task.
3. **Closing**: To close an issue automatically upon merge, link it in the PR description using `Closes #[issue-number]` or `Fixes #[issue-number]`.

