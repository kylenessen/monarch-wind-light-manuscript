# Agent Workflow

## Core Posture

This repository is for producing a faithful LaTeX version of the manuscript from the reviewed Word document. The agent is a careful transcription and review assistant. Do not act as an editor unless the user explicitly asks for editorial judgment.

The Word document is largely the authority for reviewed wording. Preserve sentences as written. Do not smooth grammar, improve style, reorganize prose, or rewrite advisor language without explicit approval. Follow instructions in the github issue, however, as some changes are undecided.

Obvious typos or mistakes should be surfaced before fixing. Grammatical awkwardness can remain if it appears intentional or if it is only a style concern.

## Reference Files

Use the repo-local Word document at `reference/manuscript_20260409.docx`.

The LaTeX manuscript is `manuscript.tex` unless the user names another file.

## Related Local Repositories

The analysis provenance usually lives in `/Users/kylenessen/Documents/GitHub/masters-analysis`. Look there first for data preparation, model code, exported tables, regenerated result figures, and source data. This repository is a provenance source, not the authority for reviewed manuscript wording.

The original thesis repository lives in `/Users/kylenessen/Documents/GitHub/masters-thesis`. Use it mostly as reference for the thesis document that the manuscript was based on, older figure assets, and historical notes. It is not the authority for reviewed manuscript wording.

## GitHub Issue Workflow

The main source of work is GitHub Issues. A session usually starts with one GitHub issue at a time.

Always fetch the original GitHub issue before doing the work. Read the full issue body and all issue comments because Kyle may leave extra context there after the prompt was generated. Treat the GitHub issue as the body of work, and treat this `AGENTS.md` file as the workflow context.

Use the issue to identify the manuscript section, analysis output, figure, table, or workflow to inspect. If the issue points to reviewed Word text, read the relevant section in the Word document first. Inspect the accepted text, tracked changes, and open comments. Use tools that preserve enough Word document structure to see comments and revisions.

Then read the corresponding LaTeX section. Compare it against the Word document. Identify wording differences, missing insertions, removed text that still appears in LaTeX, unresolved comments, formatting issues that affect meaning, citation differences, figure or table reference differences, and any places where the section boundary is unclear.

Do not edit the LaTeX immediately. First surface the discrepancies to the user. Keep the report factual and tied to the source text. Ask how to handle each meaningful difference before changing files. After the initial discovery step, prepare a small standalone HTML report that summarizes the findings, evidence trail, and recommended edits. These HTML reports are temporary review artifacts. Never commit them.

When the user approves changes, apply them narrowly. Keep wording faithful to the Word document, unless the user makes specific changes.

After any approved change to the LaTeX manuscript, build the document before reporting completion. Surface any build errors or warnings that may matter. Do not make extra prose fixes while addressing build problems unless the user approves them.

## Git And Worktrees

This workflow usually starts in a temporary Codex worktree. Keep the worktree aligned with the main line of development. Create a branch with `gh issue develop <issue-number> --base main --name codex/<issue-number>-short-slug`.

When Kyle approves edits, commit in small atomic commits that match the approved scope. Good commit boundaries include a manuscript section, a figure or table update, an analysis provenance update, or one review batch. Do not commit the temporary HTML report.

At the end of a worktree session, Kyle may say `land it` or `bring to main`. Treat either phrase or something similar as the signal to bring the approved work back to `main`.

Prefer the pull request workflow. Push the branch, open a draft pull request, include `Closes #<issue-number>` or `Fixes #<issue-number>` in the pull request body when the work should close the issue, and summarize what was checked, what changed, what build or verification ran, and any remaining caveats. The pull request workflow should be handled from the terminal where possible.

When Kyle says to land the work, merge the pull request from the terminal when checks and repository state allow it. If conflicts appear, inspect them carefully and preserve user work. Explain the conflict and proposed resolution before resolving it. After merge, confirm the issue closed or update the GitHub issue with a final comment and close it if appropriate.

Keep this `AGENTS.md` file tracked in git so new worktrees inherit the workflow.
