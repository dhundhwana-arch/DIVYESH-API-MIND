# Security policy

DIVYESH API MIND is an explicit-request client and catalog, not a credential vault, network sandbox, or security audit. Read [`docs/security.md`](docs/security.md) before using connectors or sending data to a provider.

## Reporting a vulnerability

Please do **not** post credentials, exploit details, or a suspected vulnerability in a public issue. If GitHub's private vulnerability reporting/Security Advisories feature is enabled for this repository, use that private channel. Otherwise, contact the repository maintainer privately through [GitHub](https://github.com/dhundhwana-arch) first to arrange a disclosure channel before sharing sensitive details.

There is no published response-time or remediation SLA. Please include only the minimum information needed to reproduce the issue, redact tokens and personal data, and avoid testing against third-party systems without authorization.

## Scope and safe reports

Useful reports can cover request-boundary errors, credential exposure, unsafe catalog/URL handling, or incorrect documentation that could lead to unsafe use. Provider service vulnerabilities and issues in third-party source directories are outside this project's control; report them to the relevant provider/source owner as well.
