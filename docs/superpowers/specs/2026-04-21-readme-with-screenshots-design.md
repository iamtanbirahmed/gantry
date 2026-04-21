# README with Screenshots Design

## Context

The project README is currently a two-line stub with no documentation. Gantry needs a comprehensive README that introduces the project, shows what it looks like in action, and provides getting-started instructions. Screenshots should auto-generate via `textual run --screenshot`.

## Goals

- Introduce Gantry's purpose and features clearly
- Show visual representation via screenshot
- Provide install, run, and keybindings reference
- Include mechanism to refresh screenshot as app evolves

## Design

### Screenshot Capture

- `textual run --screenshot` captures app state as SVG
- Saved to `docs/images/screenshot.svg`
- Shell script `scripts/screenshot.sh` automates capture
- Run manually anytime UI changes

### README Structure

**Sections:**
1. Title + one-liner description
2. Embedded screenshot (SVG)
3. Features (16 resource types, detail panel, search, Helm, state persistence)
4. Requirements (Python 3.11+, kubectl, helm)
5. Install instructions (`uv sync`)
6. Run commands (basic + `--debug` flag)
7. Keybindings reference table
8. Update screenshot command
9. License (MIT)

### File Structure

```
docs/
├── images/
│   └── screenshot.svg          (auto-generated)
└── superpowers/
    └── specs/
        └── 2026-04-21-readme-with-screenshots-design.md
README.md                        (updated)
scripts/
└── screenshot.sh               (new, executable)
```

## Implementation

### Step 1: Create `scripts/screenshot.sh`
Shell script with proper error handling. Makes `docs/images/` if needed.

### Step 2: Execute script
Run `bash scripts/screenshot.sh` to generate `docs/images/screenshot.svg`.

### Step 3: Update `README.md`
Full rewrite with screenshot embed, features, keybindings, and update instructions.

## Success Criteria

1. Script exits 0, `docs/images/screenshot.svg` created and non-empty
2. README renders in GitHub markdown with inline screenshot
3. Keybindings table is accurate and matches app
4. All tests still pass (no source code changes)
5. Future developers can run `scripts/screenshot.sh` to refresh
