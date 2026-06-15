# mUtils Analysis Tasks

- [x] Validate scene-style movie names before parsing in `mrenamer`.
- [x] Add a dry-run mode to `mrenamer`.
- [x] Check rename collisions before applying `mrenamer` changes.
- [x] Replace naive parenthesis stripping in `mdiffer.clean_names()`.
- [x] Reject empty extension input in `mremover`.
- [x] Align `mremover` documentation with its one-level scan behavior, or switch it to true recursion.
- [x] Decide whether files directly inside the `mremover` source directory should be processed.
- [x] Remove `sys.exit()` from reusable core functions.
- [x] Return structured results from core logic instead of capturing printed output in GUI/TUI.
- [x] Resolve `mdiffer` log/output paths relative to a predictable location or user-provided path.
- [x] Decide whether `mdiffer` duplicate matching should be case-insensitive.
- [x] Add platform guidance for symlink creation on Windows.
- [x] Add a test suite for risky parsing and planning behavior.
- [x] Add `uv` project support.
- [x] Add generated files and output directories to `.gitignore`.

## Follow-up Analysis Tasks

- [x] Add rollback or transactional handling for partial `mrenamer` failures after one rename succeeds.
- [x] Handle case-only rename behavior in `mrenamer` on case-insensitive filesystems.
- [x] Add exclusion support to `mremover` so broad recursive deletes can skip protected paths.
- [x] Decide whether `mremover` extension matching should be case-insensitive.
- [x] Clarify or adjust `mdiffer` result casing when a duplicate matches with different casing.
- [x] Avoid always overwriting `mdiffer` `log/log.txt` and `output/dupes.txt`, or make overwrite behavior explicit.
- [x] Add tests for GUI/TUI wrapper behavior.
- [x] Absolutize `msymlinker` link paths in structured results.
- [x] Document install and test commands such as `uv run pytest` in the README.
- [x] Consider moving the top-level scripts into a package/module layout if the toolset keeps growing.

## Additional Analysis Tasks

- [x] Expose `mremover` exclusions through CLI, GUI, and TUI workflows.
- [x] Require explicit confirmation when deleting with `mremover` without a preview.
- [x] Report `mrenamer` applied and rolled-back operations in structured results.
- [x] Validate each planned `mrenamer` source path before applying renames.
- [x] Document the `mrenamer` `subs` and `sample` skip policy.
- [x] Deduplicate repeated `mdiffer` duplicate results.
- [x] Use more precise `mdiffer` fallback output filenames.
- [x] Add workflow-level tests for GUI/TUI remover wrappers.
- [x] Make `mgui` safe to import in headless environments.
- [x] Keep the current flat script layout documented until the toolset grows enough to justify packaging.

## Package Layout Tasks

- [x] Move implementation modules into the `mutils` package.
- [x] Update internal imports to package-relative imports.
- [x] Add console script entry points in `pyproject.toml`.
- [x] Keep top-level compatibility wrappers for existing `python *.py` usage.
- [x] Update tests to import package modules directly.
- [x] Update README examples for package console scripts.

## Setup Command Tasks

- [x] Rename the narrow `mdiffer.setup()` helper to `ensure_output_dirs()`.
- [x] Add a `mutils-setup` console command.
- [x] Check Python version, required imports, optional GUI/TUI support, symlink capability, and writable runtime directories.
- [x] Create runtime `log/` and `output/` directories by default.
- [x] Add `--check-only` mode.
- [x] Add `--json` output mode.
- [x] Document setup command and platform-specific optional checks.
- [x] Add tests for setup checks and JSON output.

## Web GUI Tasks

- [x] Add a web GUI implementation in `mutils/web.py`.
- [x] Add a top-level compatibility wrapper named `mwui.py`.
- [x] Add a `mwui = "mutils.web:main"` console script entry point.
- [x] Choose and add the web dependency, keeping it lightweight and cross-platform.
- [x] Expose web forms for `mdiffer`, `mremover`, `mrenamer`, and `msymlinker`.
- [x] Default destructive actions to preview/dry-run mode in the web UI.
- [x] Require explicit confirmation for delete and rename actions.
- [x] Render structured tool results as HTML without relying on captured stdout.
- [x] Add request-level tests for the web routes and destructive-action safeguards.
- [x] Document `uv run mwui` and `uv run python mwui.py` usage in the README.
