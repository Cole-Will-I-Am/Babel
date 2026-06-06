# Babel Workspace Coexistence Protocol (WCP) v0.7.0

## Status
Additive layer over frozen Babel v0.1.0-v0.6.0. Defines git workspace
rules for conflict-free coexistence of human-authored .babel files and
agent-emitted .json files. No frozen field is mutated. The handoff log
semantics from v0.2.0 are unchanged; WCP only governs git attributes
and ignore patterns.

## 1. Directory Layout

    repo/
    +-- human-src/                 # human-authored .babel and .json
    |   +-- .inbox/                # transient: human drops land here
    |   +-- .processing/           # transient: gateway actively compiling
    |   +-- .processed/            # transient: compiled and ingested
    |   +-- .invalid/              # transient: compile failures archived
    +-- autonomy-output/           # agent-emitted canonical state
        +-- handoff-log/           # append-only v0.2.0 handoff log
        +-- itp-golden-v0.7.0/     # ITP reference golden files
        +-- *.md, *.json           # spec and manifest artifacts

The two top-level directories are exclusive: humans never write to
`autonomy-output/`, and agents never write to `human-src/` (except for
the four transient subdirs of human-src/ during ingestion).

## 2. .gitattributes Rules

The repository MUST contain a top-level `.gitattributes` file with:

```gitattributes
# Babel v0.7.0 WCP
*.json  binary
*.babel text eol=lf
```

- `*.json binary`: disables line-ending conversion AND disables git's
  built-in merge drivers. Git will mark conflicts as binary and require
  manual resolution, preserving the append-only ordering of handoff log
  entries. This is normative for `autonomy-output/handoff-log/*.json`.
- `*.babel text eol=lf`: forces LF line endings on commit/checkout,
  preserving the v0.6.0 BSS pragma `// babel:0.6.0` on line 1 across
  Windows, macOS, and Linux development hosts.

## 3. .gitignore Rules

The repository MUST contain a top-level `.gitignore` file with the
following Babel v0.7.0 entries:

```gitignore
# Babel v0.7.0 WCP - transient state, never commit
human-src/.inbox/*
!human-src/.inbox/.gitkeep
human-src/.processing/*
!human-src/.processing/.gitkeep
human-src/.processed/*
!human-src/.processed/.gitkeep
human-src/.invalid/*
!human-src/.invalid/.gitkeep

# Handoff log transient files
autonomy-output/handoff-log/*.tmp
autonomy-output/handoff-log/*.processing
autonomy-output/handoff-log/*.lock
```

The `.gitkeep` carve-outs preserve the four transient directories in
the working tree so the gateway agent can inotify-watch them.

## 4. .babelignore Patterns

A top-level `.babelignore` file lists patterns the gateway MUST skip
when scanning `human-src/` for ingestion:

```
autonomy-output/
.git/
*.swp
.DS_Store
```

## 5. Atomic Move Semantics

The gateway agent follows this exact sequence for every drop in
`human-src/.inbox/`:

1. INOTIFY_CREATE fires on `human-src/.inbox/<file>`.
2. Gateway atomically renames `human-src/.inbox/<file>` to
   `human-src/.processing/<file>.lock-<random8>` (random8 is 8
   lowercase hex chars to avoid collisions).
3. Gateway invokes `babel-emit < human-src/.processing/<file>.lock-<r8>`
   capturing canonical JSON bytes.
4. On success: gateway appends canonical JSON to
   `autonomy-output/handoff-log/<timestamp>-<agentid>-<random8>.json`
   via v0.2.0 atomic temp+rename; then atomically renames the
   `.processing/<file>.lock-<r8>` to `human-src/.processed/<file>`.
5. On babel-emit exit code != 0: gateway atomically renames the
   `.processing/<file>.lock-<r8>` to `human-src/.invalid/<file>` and
   writes `human-src/.invalid/<file>.error.json` with the AIC error
   schema {code, message, line, column}.

No concurrent writers exist: a single gateway agent owns `human-src/`
transitions and `autonomy-output/handoff-log/`.

## 6. Cross-References

- v0.2.0 handoff protocol: autonomy-output/babel-handoff-protocol-v0.2.0.md
- v0.6.0 HIG .babel acceptance: autonomy-output/babel-hig-v0.6.0.md
- v0.7.0 ITP acceptance: autonomy-output/babel-itp-v0.7.0.md
- v0.7.0 manifest: autonomy-output/babel-manifest-v0.7.0.json
