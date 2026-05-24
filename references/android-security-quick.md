# Android security (quick)

Full guide: [android-security.md](android-security.md) (~1800 lines). Section anchors: [INDEX-sections.md](INDEX-sections.md#android-securitymd-1805-lines).

Required before security-sensitive work:

- Server is the trust boundary; client never makes the final authorization decision.
- Play Integrity Cloud project + Play Console linking are **human/Console steps** - ask the engineer before client wiring.
- High-value actions: Play Integrity (server-decoded) with `requestHash` (Standard) or `nonce` (Classic) + tiered backend policy.
- Local root/emulator checks are supplementary only - not authoritative.

## Section routing

| Task | Open |
|------|------|
| Trust model, abuse resistance | [Device trust and abuse resistance](android-security.md#device-trust-and-abuse-resistance) |
| Cleartext, network config | [Network Security](android-security.md#network-security) |
| OkHttp / certificate pins | [Certificate Pinning](android-security.md#certificate-pinning) |
| Encrypted files, DataStore, keys | [Data Encryption at Rest](android-security.md#data-encryption-at-rest) |
| TEE, StrongBox, key specs | [Android Keystore, TEE & StrongBox](android-security.md#android-keystore-tee-strongbox) |
| BiometricPrompt, crypto auth | [Biometric Authentication](android-security.md#biometric-authentication) |
| Passkeys, Credential Manager | [Credential Manager and Sign-In](android-security.md#credential-manager-and-sign-in) |
| Advertising ID, privacy signals | [Device Identifiers and Privacy](android-security.md#device-identifiers-and-privacy) |
| API 35+ privacy platform | [Android 15+ Platform Privacy](android-security.md#android-15-platform-privacy) |
| Play Console declarations | [Play Console Data Safety](android-security.md#play-console-data-safety) |
| Integrity Standard/Classic, decode | [Play Integrity API](android-security.md#play-integrity-api) |
| Root/emulator heuristics | [Root & Emulator Detection](android-security.md#root-emulator-detection) |
| FLAG_SECURE, screenshots | [Screenshot & Screen Recording Prevention](android-security.md#screenshot-screen-recording-prevention) |
| SQLCipher / Room encryption | [Secure Database (Room 3)](android-security.md#secure-database-room-3) |
| Clipboard sensitivity | [Secure Clipboard](android-security.md#secure-clipboard) |
| WebView hardening | [WebView Security](android-security.md#webview-security) |
| `exported`, URI permissions | [Content Provider Security](android-security.md#content-provider-security) |
| R8 obfuscation | [ProGuard / R8 Hardening](android-security.md#proguard-r8-hardening) |
| GitHub Actions secrets | [CI/CD Security](android-security.md#cicd-security) |
| Pre-release checklist | [Security Checklist](android-security.md#security-checklist) |
| Catalog aliases | [Dependencies](android-security.md#dependencies) |

## Hard rules (summary)

**Required:**

- Layer controls; fail closed on errors; minimum permissions.
- Android Keystore over software-managed keys; StrongBox when available.
- Track CVEs in dependencies; run security checks in CI.

**Forbidden:**

- Logging tokens, PII, or sensitive payloads.
- Hardcoding API keys, signing material, or secrets in source.
- Caching integrity verdicts to authorize unrelated later actions on the client.

Open the full file for Standard/Classic code samples, `requestHash`/`nonce` examples, and checklist tables.
