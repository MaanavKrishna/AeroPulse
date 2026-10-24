# Security

Please report vulnerabilities privately through GitHub's "Report a vulnerability" button on
this repository (Security tab), not in a public issue. We aim to reply within 7 days.

In scope: the web app, the API, the collection pipeline, and the deployment files in
`deploy/`. Out of scope: third-party provider APIs.

Secrets (provider keys, database password, admin token) are read only from environment
variables. If you find one committed anywhere, report it as a vulnerability.
