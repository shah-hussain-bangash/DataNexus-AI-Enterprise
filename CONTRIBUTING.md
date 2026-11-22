# Contribution and engineering policy
All changes should link a requirement or documented maintenance concern. Use small pull requests, descriptive commits, ADRs for material choices, and tests that demonstrate behavior. Never commit API secrets or proprietary datasets.

## Definition of done
- Contract or migration updated when public behavior changes
- Input validation, tenant authorization and audit behavior reviewed
- Unit/integration/contract tests added as appropriate
- Failure modes and rollback documented
- Performance or cost impact considered
- README and operations notes updated
- Any benchmark reported with dataset, hardware, version and reproducible commands

Branch naming: `feat/`, `fix/`, `docs/`, `security/`.
