# Fork authorization delivery and upstream merge

The governing contract is [plan 003 revision 1.8](<auth_share_implementation_plan_updated_latest 003.md>), including D11. The target is `waqoor/langflow:main`; upstream adoption and deployment-specific assumptions remain separate.

- Preserve one bundled, automatically registered Casbin service, enabled by default, with explicit disable/replacement and provider-free standalone LFX.
- Merge upstream `595cd72a2b2021f2375fa31109af02d20bb17648` into fork baseline `5111f56569b8626a27d3b616328b1c03779bdb2a`, prioritizing incoming conflict hunks.
- Retain the required Casbin dependency beside upstream's version update. Join the existing team-sharing and variable-origin migrations with a forward-only merge revision; preserve both published migrations.
- Validate upgrades from either prior head, the required SQLite/PostgreSQL 16 and Python 3.10/3.14 matrix, eight serial authorization journeys with zero retries, and applicable inherited CI checks on the combined candidate.
- Record current results and limitations in the [verification ledger](docs/auth-team-sharing-verification.md) and [implementation audit](is_auth_done.md) before release readiness is claimed.

Merge validation is in progress. Historical acceptance does not certify the new candidate. No new authorization API, policy engine, persistence system, directory integration, or product journey is part of this work.
