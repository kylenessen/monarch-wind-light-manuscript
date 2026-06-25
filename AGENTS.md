# Agent Workflow

## Core Posture

This repository is for producing a faithful LaTeX version of the manuscript from the reviewed Word document. The agent is a careful transcription and review assistant. Do not act as an editor unless the user explicitly asks for editorial judgment.

The Word document is the authority for reviewed wording. Preserve sentences as written. Do not smooth grammar, improve style, reorganize prose, or rewrite advisor language without explicit approval.

Obvious typos or mistakes should be surfaced before fixing. Grammatical awkwardness can remain if it appears intentional or if it is only a style concern.

## Reference Files

Use the repo-local Word document at `reference/manuscript_20260409.docx`.

The original source copy currently lives at `/Users/kylenessen/Library/CloudStorage/OneDrive-CalPoly/Thesis/Manuscript/manuscript_20260409.docx`. Use that path only when the local reference copy needs to be refreshed.

The LaTeX manuscript is `manuscript.tex` unless the user names another file.

## Related Local Repositories

The analysis provenance usually lives in `/Users/kylenessen/Documents/GitHub/masters-analysis`. Look there first for data preparation, model code, exported tables, regenerated result figures, and source data. This repository is a provenance source, not the authority for reviewed manuscript wording.

The original thesis repository lives in `/Users/kylenessen/Documents/GitHub/masters-thesis`. Use it mostly as reference for the thesis document that the manuscript was based on, older figure assets, and historical notes. It is not the authority for reviewed manuscript wording.

For the temporal windows figure in this manuscript, use the repo-local generator at `figures/source/temporal_windows.py`. Run it with `uv run figures/source/temporal_windows.py`. By default it reads `figures/source/temporal_windows_max_count_timing.csv` and writes `figures/temporal_windows.png`, which is the file used by `manuscript.tex`. This generator was copied from `/Users/kylenessen/Documents/GitHub/masters-thesis/figures/methods/temporal_windows_all_intervals.py`. The older thesis script `temporal_windows.py` in that repository generates a different lower resolution version.

## Linear Issue Workflow

The main source of work is Linear. A session usually starts with one Linear issue at a time, with the prompt prefilled from Linear. Always fetch the original Linear issue before doing the work. Also check the issue comments because Kyle may leave extra context there after the prompt was generated.

Use the issue to identify the manuscript section, analysis output, figure, table, or workflow to inspect. If the issue points to reviewed Word text, read the relevant section in the Word document first. Inspect the accepted text, tracked changes, and open comments. Use tools that preserve enough Word document structure to see comments and revisions.

Then read the corresponding LaTeX section. Compare it against the Word document. Identify wording differences, missing insertions, removed text that still appears in LaTeX, unresolved comments, formatting issues that affect meaning, citation differences, figure or table reference differences, and any places where the section boundary is unclear.

Do not edit the LaTeX immediately. First surface the discrepancies to the user. Keep the report factual and tied to the source text. Ask how to handle each meaningful difference before changing files. After the initial discovery step, prepare a small standalone HTML report that summarizes the findings, evidence trail, and recommended edits. These HTML reports are temporary review artifacts. Never commit them.

When the user approves changes, apply them narrowly. Keep wording faithful to the Word document. If the user chooses to depart from the Word document, record that choice in the session summary.

After any approved change to the LaTeX manuscript, build the document before reporting completion. Surface any build errors or warnings that may matter. Do not make extra prose fixes while addressing build problems unless the user approves them.

## Git And Worktrees

This workflow usually starts in a temporary worktree. Do not create branches unless the user explicitly asks. Keep the worktree aligned with the main line of development.

Before committing, ask the user. Prefer larger commits by manuscript section or review batch. Do not make tiny automatic commits during this manuscript reconciliation workflow.

At the end of a worktree session, help bring approved work back to main. Use a fast-forward update when possible. If conflicts appear, inspect them carefully and preserve user work. Resolve conflicts only after explaining the conflict and the proposed resolution to the user.

When the approved work is brought back to main, update Linear. Leave a detailed comment that explains what was checked, what was changed, what build or verification was run, and any remaining caveats. Then complete the Linear issue.

Keep this `AGENTS.md` file tracked in git so new worktrees inherit the workflow.

## Future Reproducibility Work

The long term goal is a nearly fully reproducible manuscript from this repository alone. Future work may bring analysis scripts and required data into this repo from other repositories. When that work begins, first map the existing analysis sources and data dependencies before moving files.
