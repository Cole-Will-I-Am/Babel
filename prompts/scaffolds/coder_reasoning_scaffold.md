# Babel Coder Reasoning Scaffold

1. **Locate the target.** From the approved artifacts, identify which spec
   section now needs a reference implementation (e.g. AIC CLI tools, BSS
   `.babel` compiler, parser/validator, conformance test vectors).
2. **Survey existing code.** Read `reference/` and `orchestrator/canonical.py`.
   Reuse the canonical serializer; extend existing modules instead of rewriting.
3. **Implement literally.** Code exactly what the spec states. Where ambiguous,
   take the most literal reading and record the assumption.
4. **Test it.** Add a `unittest` test under `reference/tests/` covering the
   spec's stated behavior and any conformance vectors.
5. **Verify mentally.** Confirm determinism (stable ordering, byte-exact output,
   no randomness/clock) and that tests would pass as written.
6. **Hand off.** Summarize modules+tests added, assumptions, and the next gap.
