# Security

This integration talks to U-tec / Xthings **cloud** APIs. It does not ship mobile-app client certificates, APKs, or Wi-Fi passwords.

- Home Assistant stores the Xthings account password and OpenAPI tokens in its config entry. Treat backups as secret.
- Diagnostics download redacts credentials and tokens.
- Report vulnerabilities privately if you can (GitHub Security Advisories once the repo is public). Do not open a public issue with tokens, webhook secrets, or lock credentials.
