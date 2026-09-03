# How to contribute to Langflow

Thank you for your interest in contributing!

## Team-sharing work in this fork

For the approved `auth_share_implementation_plan.md` implementation, write only
to `feat/auth-team-sharing` in `waqoor/langflow` (repository ID `1353667234`,
formerly addressed as `yazeedhasan97/langflow`). The delivery PR targets this
fork's `main`; implementation work must not push directly to main/master, merge
the PR, or modify the upstream repository.

The [implementation and verification record](docs/auth-team-sharing-verification.md)
distinguishes completed work from pending integration and tests. Its existence
does not indicate the feature is ready to merge.

The upstream contribution instructions below apply to an optional, separately
requested submission to `langflow-ai/langflow`. They do not change this fork's
implementation destination.

## How to Contribute

1. Fork the [Langflow GitHub repository](https://github.com/langflow-ai/langflow).
2. Create a new branch for your changes.
3. Open a GitHub pull request against the active `release-X.Y.Z` release candidate branch.
Do not target `main`.
For example, if the latest released version is `1.8.0`, your pull request should target the `release-1.9.0` branch.
Include a clear title and description.
Reference any issues fixed, for example `Fixes #1234`.
Ensure your PR title follows [semantic commit conventions](https://www.conventionalcommits.org/).
4. A maintainer will review your PR and may request changes.

## Development Environment Setup

For detailed instructions on setting up your local development environment, see [DEVELOPMENT.md](./DEVELOPMENT.md).

## Documentation Contributions

Langflow documentation is built with [Docusaurus](https://docusaurus.io/).
For setup instructions, see [DEVELOPMENT.md](./DEVELOPMENT.md).

## Additional Guides

- [Contribute Bundles](./docs/docs/Contributing/contributing-bundles.mdx)
- [Contribute Components](./docs/docs/Contributing/contributing-components.mdx)
- [Contribute Tests](./docs/docs/Contributing/contributing-component-tests.mdx)
- [Contribute Templates](./docs/docs/Contributing/contributing-templates.mdx)

Thank you for helping improve Langflow!
