# Security and privacy

- Do not commit user recordings, model caches, API keys, auth tokens, or personal data.
- ClutchSift processes local user-supplied media with FFmpeg. Update FFmpeg and avoid untrusted recordings when possible.
- Export targets are user-selected. Existing files may be replaced if the same export name is reused; the original source path is specifically protected.
- Ollama calls `http://127.0.0.1:11434/api/chat` only. If you modify model providers, clearly document any remote data transfer and require opt-in.
- Generated subtitles and titles may contain errors and should be reviewed before publication.
- Report a vulnerability privately to repository maintainers rather than publishing exploitable details in public issues.
