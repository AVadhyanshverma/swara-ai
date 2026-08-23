# Python Environment Rule

When working with Python in this directory (`memory`), ALWAYS use the virtual environment located at `../.venv` (i.e., `/home/adhyansh/Projects/Reverie/.venv`).

Do not use the global Python interpreter. Run Python commands and scripts using the virtual environment's executable or by activating it first.


# Agent Rules and Workflows

## Rule: Continuous Work Logging
Every time a significant change, feature addition, or debugging session is completed, you MUST document the work done.
1. Create a new markdown file in the `.mds/` directory.
2. The filename must follow the format: `{now_timestamp}.md` (e.g., `20260821_153000.md`).
3. Summarize all code changes, architecture decisions, and proxy routing modifications made during the session.

