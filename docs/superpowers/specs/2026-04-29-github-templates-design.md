# GitHub Issue & PR Templates Design

## Context

Gantry project lacks issue and PR templates. Contributors currently submit issues/PRs without structure, making it harder to triage bugs, understand feature requests, or verify changes. Project uses Conventional Commits (`fix:`, `feat:`, `chore:`) and has Claude bot integration. Templates enforce consistent reporting and improve contributor experience.

## Solution

Create 5 markdown templates under `.github/`:

1. **Bug Report** — standardized bug submission
2. **Feature Request** — structured feature proposals
3. **Documentation** — for doc improvements
4. **Question** — Q&A issues
5. **PR Template** — enforces summary/test plan/checklist

### Issue Templates

Each issue template includes:
- YAML frontmatter with `name`, `about`, `labels`, `title` (GitHub auto-applies labels, pre-fills title)
- Markdown sections with guidance text

**Bug Report**
- Description (what happened)
- Steps to Reproduce
- Expected vs Actual Behavior
- Environment (OS, Python, K8s, Helm, Gantry versions)
- Logs/Screenshots

**Feature Request**
- Problem/Motivation (why needed)
- Proposed Solution
- Alternatives Considered
- Additional Context

**Documentation**
- What's Missing or Incorrect
- Location (file/section)
- Suggested Fix

**Question**
- Question
- Context
- What You've Tried

### PR Template

Markdown only (no frontmatter — auto-loaded by GitHub).

Sections:
- **Summary** — 1-3 sentences describing changes
- **Changes** — bulleted list of specific modifications
- **Type of Change** — checklist for bug fix / new feature / breaking change / docs
- **Test Plan** — how reviewers can verify
- **Checklist** — tests pass / docs updated / breaking change noted

### File Structure

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.md
│   ├── feature_request.md
│   ├── documentation.md
│   └── question.md
└── PULL_REQUEST_TEMPLATE.md
```

## Testing

1. Create feature branch
2. Write all 5 templates
3. Commit to git
4. Push to GitHub and verify:
   - New issue page shows all 4 issue templates in dropdown
   - Each template auto-applies correct label
   - PR template auto-populates when creating PR

## Trade-offs

- **Markdown vs YAML Forms**: Chose markdown for simplicity and compatibility (works everywhere). YAML forms offer richer UX but require GitHub and have steeper learning curve.
- **5 templates vs 2 (bug/feature)**: Q&A and documentation are common issue types. Separating them reduces noise in bug/feature discussions.
- **Mandatory fields**: Templates use guidance text, not GitHub Forms (which enforce required fields). This balances structure with flexibility.
