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

---

## Python Data Workflow Execution

Our pipeline operations are structured as modular Python scripts rather than exploratory notebooks. This ensures automated reproducibility, reliability under cron scheduling, and error traceability.

### 1. How to Execute the Script

Activate your virtual environment and run the pipeline script directly from the project root:

```bash
# Activate environment (Windows)
venv\Scripts\Activate.ps1

# Run the data pipeline
python scripts/data_workflow.py
```

To run and capture the console logging outputs in a text file:
```bash
python scripts/data_workflow.py > output/sample_run.txt
```

### 2. Functional Architecture & Responsibilities

The pipeline follows the **Three-Function Pattern** dividing ingestion, calculation, and output:

1. **`ingest_data(filepath)`**:
   - **Role**: Reads the CSV file from disk and loads it into a pandas DataFrame.
   - **Inputs**: Path to the raw CSV file (`data/raw/sample.csv`).
   - **Outputs**: Loaded pandas DataFrame.
   - **Error Handling**: Verifies file existence and logs file errors (`FileNotFoundError`, `EmptyDataError`) before raising.
2. **`process_data(df)`**:
   - **Role**: Performs duplicate removal, fills missing fields, and implements feature calculations.
   - **Inputs**: Raw pandas DataFrame.
   - **Outputs**: Cleaned and transformed DataFrame.
   - **Transformations**:
     - Removes exact duplicate records via `drop_duplicates()`.
     - Fills missing numeric values with their column-wise median values to prevent skewing analytics.
     - Computes the picking performance metric `items_per_minute` (calculates items prepared per minute of picking time, protecting against division by zero by clipping pick durations to a minimum of 1 second).
3. **`output_results(df, output_path)`**:
   - **Role**: Writes the final processed dataset to disk and outputs statistics to the console.
   - **Inputs**: Transformed DataFrame and output target path.
   - **Outputs**: Saved CSV file (`output/processed.csv`) and console log messages.

### 3. How to Modify for New Datasets

To run the pipeline on a new raw dataset:
1. Place your raw dataset inside the `data/raw/` folder (e.g., `data/raw/new_transactions.csv`).
2. Open `scripts/data_workflow.py` and modify the hard-coded configuration constants at the top:
   ```python
   INPUT_FILE = "data/raw/new_transactions.csv"
   OUTPUT_FILE = "output/processed_new_transactions.csv"
   ```
3. If the new dataset has different numerical column schemas, the cleaning loop inside `process_data` will automatically identify and compute their medians. If different formulas or transformations are required, update the processing steps inside the `process_data(df)` function only.


