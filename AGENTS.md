# Agent instructions

This file is a map, not the policy engine.

- Read `docs/ARCHITECTURE.md` before changing enforcement logic.
- Never weaken fail-closed behavior or governance self-protection.
- Never delete or relax tests to make validation pass.
- Changes to command rules require tests for both deny and allow behavior.
- Run `python -m unittest discover -s tests -v` before reporting completion.
- Treat `README.md` source attribution as part of the product contract.

