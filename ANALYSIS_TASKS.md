# mUtils Analysis Tasks

- [x] Validate scene-style movie names before parsing in `mrenamer`.
- [x] Add a dry-run mode to `mrenamer`.
- [x] Check rename collisions before applying `mrenamer` changes.
- [x] Replace naive parenthesis stripping in `mdiffer.clean_names()`.
- [x] Reject empty extension input in `mremover`.
- [ ] Align `mremover` documentation with its one-level scan behavior, or switch it to true recursion.
- [ ] Decide whether files directly inside the `mremover` source directory should be processed.
- [ ] Remove `sys.exit()` from reusable core functions.
- [ ] Return structured results from core logic instead of capturing printed output in GUI/TUI.
- [ ] Resolve `mdiffer` log/output paths relative to a predictable location or user-provided path.
- [ ] Decide whether `mdiffer` duplicate matching should be case-insensitive.
- [ ] Add platform guidance for symlink creation on Windows.
- [x] Add a test suite for risky parsing and planning behavior.
- [x] Add `uv` project support.
- [x] Add generated files and output directories to `.gitignore`.
