# Security

Inspect only trusted Git repositories, executables and configuration. Offline `--stdin` mode executes no Git command. Remote mode intentionally contacts the selected public HTTPS server; it is not a Git-config sandbox. Never embed credentials in remote URLs. Default output hides ref names; `--show-names` may disclose private naming. Review any output before sharing.

No automated mutation or upload. Report vulnerabilities using GitHub private vulnerability reporting if available; otherwise open a minimal issue without secrets, logs, private names or paths. Do not publish sensitive reproductions. No response SLA is promised.
