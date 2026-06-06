# Babel Toolchain Integration Contract (TIC) v0.7.0

## Status
Additive layer over frozen Babel v0.1.0-v0.6.0. Defines a deterministic
agent package format for distributing frozen AIC toolchains. No frozen
field is mutated. The handoff log entries are unchanged; TIC operates
at packaging and distribution boundaries only.

## 1. Package Filename Convention

Every TIC package MUST be named:

    {agent-name}-{platform}.tar.babel

Where `platform` is one of:

    linux-amd64
    darwin-arm64
    windows-amd64

The platform triplet is mandatory and is repeated inside the manifest
(see section 3). Agents MUST refuse to unpack a package whose filename
platform does not match the host platform.

## 2. Reproducible Tar Construction

Packages MUST be created with the following tar invocation, byte-for-byte:

    tar --mtime=0 --owner=0 --group=0 --numeric-owner \
        --mode=go=rX,u=rwX \
        -cf {agent-name}-{platform}.tar.babel \
        manifest.json binaries/ self-check.sh

The flags in this order are normative. The flags guarantee:
- `--mtime=0`: zeroed modification time
- `--owner=0 --group=0 --numeric-owner`: numeric uid/gid, no name lookups
- `--mode=go=rX,u=rwX`: deterministic permission bits

The tar file itself is not hashed for identity. Identity is the canonical
manifest.json (see section 4).

## 3. Manifest Fields (v0.2.0 Canonical)

```json
{
  "$schema": "https://babel-protocol.org/schemas/v0.2.0/manifest.json",
  "manifest_id": "tic-{agent-name}-{platform}",
  "manifest_version": "0.7.0",
  "spec_version": "0.7.0",
  "platform": "linux-amd64",
  "agent_name": "{agent-name}",
  "frozen_manifest_ref": "autonomy-output/babel-manifest-v0.6.0.json",
  "artifacts": [
    { "path": "binaries/babel-emit",   "role": "executable" },
    { "path": "binaries/babel-validate", "role": "executable" },
    { "path": "binaries/babel-hash",  "role": "executable" },
    { "path": "self-check.sh",        "role": "script" }
  ],
  "created_by": "minimadmax",
  "created_at": "2026-06-06T21:30:00Z"
}
```

`platform` is REQUIRED. The agent_name must match the filename prefix.

## 4. Self-Check Invocation

The `self-check.sh` script MUST conform to the following constraints:

- Shebang: `#!/bin/sh` (POSIX shell only, no bashisms)
- Uses ONLY packaged binaries resolved as `./binaries/babel-hash` and
  `./binaries/babel-validate`
- No external dependencies (no curl, jq, python, awk, sed beyond POSIX,
  no environment lookups beyond $PATH for the two packaged binaries)
- Reads manifest.json from the package root, pipes its bytes to
  `./binaries/babel-hash -` (stdin), compares hex output to a precomputed
  golden hash emitted in a one-line comment: `# golden: <hex>`
- Exit codes: 0 = hash matches, 1 = hash mismatch, 2 = missing binary

## 5. Package Layout

    {agent-name}-{platform}.tar.babel
    +-- manifest.json
    +-- binaries/
    |   +-- babel-emit       (statically linked, platform-matched)
    |   +-- babel-validate   (statically linked, platform-matched)
    |   +-- babel-hash       (statically linked, platform-matched)
    +-- self-check.sh        (POSIX, shebang #!/bin/sh)
    +-- README.txt           (optional human-readable notes)

## 6. Unpack and Verify

```sh
mkdir -p {agent}-work && cd {agent}-work
tar -xf ../{agent-name}-{platform}.tar.babel
./self-check.sh || { echo "self-check failed"; exit 1; }
```

The unpacked manifest.json is then hashed externally with the host's
babel-hash for cross-package identity comparison.

## 7. Rollback Path

TIC packages are immutable. To roll back, the previous version's package
is fetched via the URL/path stored in `frozen_manifest_ref` of the prior
manifest. Agents MUST keep at least the prior version's package on disk
or in a local cache until the new version is verified by self-check and
one successful ITP pass.

## 8. Cross-References

- v0.6.0 AIC CLI contracts: autonomy-output/babel-aic-v0.6.0.md
- v0.6.0 manifest: autonomy-output/babel-manifest-v0.6.0.json
- v0.7.0 manifest: autonomy-output/babel-manifest-v0.7.0.json
- v0.7.0 ITP: autonomy-output/babel-itp-v0.7.0.md
