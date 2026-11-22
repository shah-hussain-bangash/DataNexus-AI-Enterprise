# Security policy
**Status:** architecture-stage repository; no claim of a production security review.

Do not submit vulnerabilities containing live keys, exploit traffic, or confidential data to public issues. Contact the repository maintainer privately through their GitHub profile.

## Security design principles
- Deny by default; authenticate at the edge; authorize every resource/tool action.
- Isolate tenant data at API, query, storage and event boundaries.
- Use short-lived credentials and managed secret storage.
- Encrypt in transit and at rest; define retention and deletion behavior.
- Treat prompts, documents and event payloads as untrusted.
- Agent writes require scoped tools and human approval.
- Record audit evidence without logging secrets or unnecessary personal data.

Required before production: threat-model review, SAST/dependency and secret scanning, authorization tests, incident response, third-party license review and independent validation.
