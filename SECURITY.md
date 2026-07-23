# Security policy

## Supported versions

Security fixes are applied to the latest release on the default branch.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Use GitHub's
private vulnerability reporting feature after it is enabled for this repository.
Until then, contact the maintainer privately through the contact method listed on
their GitHub profile.

Include the affected version, reproduction steps, impact, and any suggested
mitigation. You should receive an acknowledgement within seven days.

## Current security model

The desktop and browser modes are designed for a single trusted user. Browser
mode listens on `127.0.0.1` by default. Setting `ALLOW_NETWORK_ACCESS=true`
exposes the application to the local network without authentication and should
only be used temporarily on a trusted network.

Documents, extracted attachment text, chat history, embeddings, and logs are
stored locally without application-level encryption. Protect the host account
and disk accordingly. A remote `OLLAMA_BASE_URL` sends prompts and retrieved
content to that endpoint.
