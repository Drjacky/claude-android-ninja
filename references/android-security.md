# Android Security

Security guide for Android apps, aligned with our modular architecture.

## Table of Contents
1. [Modern device trust and abuse resistance](#modern-device-trust-and-abuse-resistance)
2. [Network Security](#network-security)
3. [Certificate Pinning](#certificate-pinning)
4. [Data Encryption at Rest](#data-encryption-at-rest)
5. [Android Keystore, TEE & StrongBox](#android-keystore-tee--strongbox)
6. [Biometric Authentication](#biometric-authentication)
7. [Credential Manager and Sign-In](#credential-manager-and-sign-in)
8. [Device Identifiers and Privacy](#device-identifiers-and-privacy)
9. [Play Console Data Safety](#play-console-data-safety)
10. [Play Integrity API](#play-integrity-api)
11. [Root & Emulator Detection](#root--emulator-detection)
12. [Screenshot & Screen Recording Prevention](#screenshot--screen-recording-prevention)
13. [Secure Database (Room)](#secure-database-room)
14. [Secure Clipboard](#secure-clipboard)
15. [WebView Security](#webview-security)
16. [Content Provider Security](#content-provider-security)
17. [ProGuard / R8 Hardening](#proguard--r8-hardening)
18. [CI/CD Security](#cicd-security)
19. [Security Checklist](#security-checklist)

## Dependencies

Security-related libraries available in the version catalog:

- `androidx-biometric` - BiometricPrompt (fingerprint, face)
- `androidx-security-crypto` - EncryptedSharedPreferences, EncryptedFile
- `play-integrity` - Play Integrity API (device/app attestation)
- `sqlcipher-android` - SQLCipher for encrypted Room databases

Add them to your module as needed, following [dependencies.md → Adding a New Dependency](dependencies.md#adding-a-new-dependency).

## Modern device trust and abuse resistance

Use this section when you need **strong assurance** that a sensitive action (login, payment, account change) really comes from **your Play-distributed app** on a **trustworthy device**, not from a modified client or replayed token.

### Why client-only "root" style checks are not enough

Heuristics that look for `su`, Magisk paths, or suspicious packages can still be useful as **telemetry**, but they are **easy to evade** and **tamperable** on the client. An implementation that only does local checks and then allows or blocks in the app is a weak trust boundary. **Do not** treat "root detected" / "not detected" as the only input for high-value flows.

### What to decide instead

Ask whether you can trust **this combination** for **this action**:

- The **app binary** matches what Play expects (**app integrity**).
- The **install and account context** are legitimate (**licensing / account signals**).
- The **device environment** meets your policy (**device integrity** and optional signals).
- The **integrity token** applies to **this specific server request** (binding via `requestHash` for Standard API or `nonce` for Classic - see [Play Integrity API](#play-integrity-api)).

That matches how [Play Integrity API](https://developer.android.com/google/play/integrity/overview) is designed: **server-verifiable** signals, not a single client-side boolean.

### What to implement (order of responsibility)

1. **Backend is authoritative.** Decrypt and verify tokens on the server; apply **tiered** policy (allow, step-up auth, rate limits, or deny **only** the sensitive operation). The client must not be the only place that enforces access to protected APIs.
2. **Use Play Integrity** for apps distributed on Google Play when you need that assurance. Integrate the **Standard** flow for frequent checks (prepare token provider, then request with `requestHash`) or **Classic** for rare, high-value checks (`nonce`) - details in [Play Integrity API](#play-integrity-api).
3. **Bind each token to the action** so a token minted for one request cannot be replayed for another (hash a canonical representation of the protected request; never put secrets in plaintext into the hash field).
4. **Roll out enforcement gradually:** log verdicts and error rates first, then tighten rules so you avoid blocking legitimate users by surprise.
5. **Combine with cryptography where appropriate:** Android Keystore-backed keys for device-bound signing or encryption of high-value operations (see [Android Keystore, TEE & StrongBox](#android-keystore-tee--strongbox)).
6. **Treat optional runtime signals** (overlays, accessibility abuse patterns, automation) as **risk inputs** feeding your policy or fraud engine, not as the sole gate unless product requirements demand it.

### Official reference

- [Play Integrity API overview](https://developer.android.com/google/play/integrity/overview) (what the API provides and recommended practices)

## Network Security

### Network Security Configuration

Create `res/xml/network_security_config.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <!-- Block all cleartext (HTTP) traffic -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>

    <!-- Debug overrides (only in debug builds) -->
    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />
        </trust-anchors>
    </debug-overrides>
</network-security-config>
```

Reference in `AndroidManifest.xml`:

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ... >
</application>
```

### OkHttp Security Configuration

```kotlin
// core/network/di/NetworkModule.kt
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        return OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            // TLS 1.2+ only (default on API 24+, but explicit is better)
            .connectionSpecs(listOf(ConnectionSpec.MODERN_TLS))
            // Redirect policy
            .followRedirects(true)
            .followSslRedirects(true)
            .build()
    }
}
```

### Preventing Man-in-the-Middle Attacks

- Enforce HTTPS for all API endpoints (via network security config)
- Use certificate pinning for critical endpoints (see below)
- Validate server certificates
- Disable cleartext traffic in production

## Certificate Pinning

Pin your server's public key hash to prevent MITM attacks even with compromised CAs.

### Option 1: Network Security Config (Recommended)

```xml
<!-- res/xml/network_security_config.xml -->
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>

    <domain-config>
        <domain includeSubdomains="true">api.example.com</domain>
        <pin-set expiration="2027-01-01">
            <!-- Primary pin (leaf certificate) -->
            <pin digest="SHA-256">base64EncodedSHA256PinHere=</pin>
            <!-- Backup pin (intermediate or root CA) -->
            <pin digest="SHA-256">base64EncodedBackupPinHere=</pin>
        </pin-set>
    </domain-config>

    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />
        </trust-anchors>
    </debug-overrides>
</network-security-config>
```

### Option 2: OkHttp Certificate Pinner (Programmatic)

For more control (e.g., dynamic pins, per-request):

```kotlin
// core/network/di/NetworkModule.kt
@Provides
@Singleton
fun provideOkHttpClient(): OkHttpClient {
    val certificatePinner = CertificatePinner.Builder()
        .add(
            "api.example.com",
            "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" // Primary
        )
        .add(
            "api.example.com",
            "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=" // Backup
        )
        .build()

    return OkHttpClient.Builder()
        .certificatePinner(certificatePinner)
        .connectionSpecs(listOf(ConnectionSpec.MODERN_TLS))
        .build()
}
```

### Extracting Pin Hashes

```bash
# From a live server
openssl s_client -servername api.example.com -connect api.example.com:443 \
  2>/dev/null | openssl x509 -pubkey -noout | \
  openssl pkey -pubin -outform der | \
  openssl dgst -sha256 -binary | openssl enc -base64

# From a certificate file
openssl x509 -in server.crt -pubkey -noout | \
  openssl pkey -pubin -outform der | \
  openssl dgst -sha256 -binary | openssl enc -base64
```

### Best Practices

- **Always include a backup pin** (intermediate or root CA) to avoid lockout during cert rotation
- **Set expiration dates** on pin-sets so expired pins don't brick the app
- **Use network security config** (Option 1) for static pins, OkHttp for dynamic pins
- **Monitor pin failures** in production: log pin mismatch events to crash reporter
- **Test before release**: Verify pins work in staging environment

## Data Encryption at Rest

### EncryptedSharedPreferences

For storing small secrets (tokens, keys, flags):

```kotlin
// core/data/storage/SecurePreferences.kt
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SecurePreferences @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .setRequestStrongBoxBacked(true) // Use StrongBox if available
        .build()

    private val prefs = EncryptedSharedPreferences.create(
        context,
        "secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun saveAuthToken(token: String) {
        prefs.edit().putString(KEY_AUTH_TOKEN, token).apply()
    }

    fun getAuthToken(): String? = prefs.getString(KEY_AUTH_TOKEN, null)

    fun saveRefreshToken(token: String) {
        prefs.edit().putString(KEY_REFRESH_TOKEN, token).apply()
    }

    fun getRefreshToken(): String? = prefs.getString(KEY_REFRESH_TOKEN, null)

    fun clearAll() {
        prefs.edit().clear().apply()
    }

    companion object {
        private const val KEY_AUTH_TOKEN = "auth_token"
        private const val KEY_REFRESH_TOKEN = "refresh_token"
    }
}
```

### EncryptedFile

For larger encrypted data (documents, cached files):

```kotlin
import androidx.security.crypto.EncryptedFile
import androidx.security.crypto.MasterKey

class SecureFileStorage @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    fun writeSecureFile(filename: String, data: ByteArray) {
        val file = File(context.filesDir, filename)
        if (file.exists()) file.delete()

        val encryptedFile = EncryptedFile.Builder(
            context,
            file,
            masterKey,
            EncryptedFile.FileEncryptionScheme.AES256_GCM_HKDF_4KB
        ).build()

        encryptedFile.openFileOutput().use { output ->
            output.write(data)
        }
    }

    fun readSecureFile(filename: String): ByteArray? {
        val file = File(context.filesDir, filename)
        if (!file.exists()) return null

        val encryptedFile = EncryptedFile.Builder(
            context,
            file,
            masterKey,
            EncryptedFile.FileEncryptionScheme.AES256_GCM_HKDF_4KB
        ).build()

        return encryptedFile.openFileInput().use { input ->
            input.readBytes()
        }
    }
}
```

### Bank-Level Encryption (AES-256-GCM)

For custom encryption when you need full control (e.g., encrypting data before sending to server):

```kotlin
// core/data/crypto/AesGcmEncryption.kt
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class AesGcmEncryption {

    companion object {
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
        private const val GCM_TAG_LENGTH = 128
        private const val GCM_IV_LENGTH = 12
    }

    fun getOrCreateKey(alias: String): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE)
        keyStore.load(null)

        keyStore.getEntry(alias, null)?.let { entry ->
            return (entry as KeyStore.SecretKeyEntry).secretKey
        }

        val keyGenerator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            ANDROID_KEYSTORE
        )

        val spec = KeyGenParameterSpec.Builder(
            alias,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
            .setIsStrongBoxBacked(isStrongBoxAvailable())
            .setUserAuthenticationRequired(false)
            .build()

        keyGenerator.init(spec)
        return keyGenerator.generateKey()
    }

    fun encrypt(data: ByteArray, key: SecretKey): ByteArray {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, key)

        val iv = cipher.iv
        val encrypted = cipher.doFinal(data)

        // Prepend IV to ciphertext: [IV (12 bytes)][ciphertext + tag]
        return iv + encrypted
    }

    fun decrypt(encryptedData: ByteArray, key: SecretKey): ByteArray {
        val iv = encryptedData.copyOfRange(0, GCM_IV_LENGTH)
        val ciphertext = encryptedData.copyOfRange(GCM_IV_LENGTH, encryptedData.size)

        val cipher = Cipher.getInstance(TRANSFORMATION)
        val spec = GCMParameterSpec(GCM_TAG_LENGTH, iv)
        cipher.init(Cipher.DECRYPT_MODE, key, spec)

        return cipher.doFinal(ciphertext)
    }

    private fun isStrongBoxAvailable(): Boolean {
        return try {
            val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE)
            keyStore.load(null)
            android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.P
        } catch (_: Exception) {
            false
        }
    }
}
```

### Software Fallback (No Hardware Security Module)

When the device lacks TEE/StrongBox (rare but possible on very old devices):

```kotlin
// core/data/crypto/SoftwareEncryption.kt
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec
import java.security.SecureRandom

class SoftwareEncryption {

    fun generateKey(): ByteArray {
        val keyGenerator = KeyGenerator.getInstance("AES")
        keyGenerator.init(256, SecureRandom())
        return keyGenerator.generateKey().encoded
    }

    fun encrypt(data: ByteArray, keyBytes: ByteArray): ByteArray {
        val key = SecretKeySpec(keyBytes, "AES")
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key)
        val iv = cipher.iv
        val encrypted = cipher.doFinal(data)
        return iv + encrypted
    }

    fun decrypt(encryptedData: ByteArray, keyBytes: ByteArray): ByteArray {
        val iv = encryptedData.copyOfRange(0, 12)
        val ciphertext = encryptedData.copyOfRange(12, encryptedData.size)
        val key = SecretKeySpec(keyBytes, "AES")
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(128, iv))
        return cipher.doFinal(ciphertext)
    }
}
```

**Warning:** Store the software-generated key securely (e.g., derive from user password via PBKDF2). Never hardcode keys or store them in `SharedPreferences` in plaintext.

## Android Keystore, TEE & StrongBox

### What They Are

- **Android Keystore**: System-level key storage backed by hardware (when available). Keys never leave the secure hardware.
- **TEE (Trusted Execution Environment)**: An isolated processing environment (e.g., ARM TrustZone) that runs alongside Android but is isolated from the main OS. Most modern Android devices have TEE support.
- **StrongBox**: A dedicated secure element (separate hardware chip). More secure than TEE because the key material is in a tamper-resistant chip, not just an isolated CPU mode. Available since API 28 on devices that have a dedicated secure element.

### How They Protect

| Feature                 | TEE                  | StrongBox                 |
|-------------------------|----------------------|---------------------------|
| Hardware isolation      | CPU trust zone       | Dedicated chip            |
| Side-channel resistance | Limited              | High                      |
| Tamper resistance       | Software-level       | Physical tamper-resistant |
| Key extraction          | Difficult            | Near impossible           |
| Availability            | Most devices API 24+ | API 28+ (select devices)  |

### Using Hardware-Backed Keys

```kotlin
// core/data/crypto/KeystoreManager.kt
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties

class KeystoreManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }

    fun createKey(
        alias: String,
        requireBiometric: Boolean = false,
        requireStrongBox: Boolean = false
    ): SecretKey {
        if (keyStore.containsAlias(alias)) {
            return (keyStore.getEntry(alias, null) as KeyStore.SecretKeyEntry).secretKey
        }

        val builder = KeyGenParameterSpec.Builder(
            alias,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)

        if (requireBiometric) {
            builder.setUserAuthenticationRequired(true)
            builder.setUserAuthenticationParameters(
                0, // Every use requires auth
                KeyProperties.AUTH_BIOMETRIC_STRONG
            )
            builder.setInvalidatedByBiometricEnrollment(true)
        }

        if (requireStrongBox && isStrongBoxAvailable()) {
            builder.setIsStrongBoxBacked(true)
        }

        val keyGenerator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            "AndroidKeyStore"
        )
        keyGenerator.init(builder.build())
        return keyGenerator.generateKey()
    }

    fun deleteKey(alias: String) {
        if (keyStore.containsAlias(alias)) {
            keyStore.deleteEntry(alias)
        }
    }

    fun isStrongBoxAvailable(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            context.packageManager.hasSystemFeature(PackageManager.FEATURE_STRONGBOX_KEYSTORE)
        } else {
            false
        }
    }

    fun isHardwareBackedKeystore(): Boolean {
        // TEE-backed on most devices API 24+
        return try {
            val keyInfo = keyStore.getKey("test_key", null)
            // Key generation test passed = hardware backed
            true
        } catch (_: Exception) {
            false
        }
    }
}
```

### DI Integration

```kotlin
// core/data/di/SecurityModule.kt
@Module
@InstallIn(SingletonComponent::class)
object SecurityModule {

    @Provides
    @Singleton
    fun provideSecurePreferences(
        @ApplicationContext context: Context
    ): SecurePreferences = SecurePreferences(context)

    @Provides
    @Singleton
    fun provideKeystoreManager(
        @ApplicationContext context: Context
    ): KeystoreManager = KeystoreManager(context)

    @Provides
    @Singleton
    fun provideAesGcmEncryption(): AesGcmEncryption = AesGcmEncryption()
}
```

## Biometric Authentication

### BiometricPrompt Setup

```kotlin
// core/ui/biometric/BiometricAuthenticator.kt
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricManager.Authenticators
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity

class BiometricAuthenticator {

    fun canAuthenticate(context: Context): BiometricStatus {
        val biometricManager = BiometricManager.from(context)

        return when (biometricManager.canAuthenticate(
            Authenticators.BIOMETRIC_STRONG or Authenticators.BIOMETRIC_WEAK
        )) {
            BiometricManager.BIOMETRIC_SUCCESS -> BiometricStatus.Available
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE -> BiometricStatus.NoHardware
            BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE -> BiometricStatus.HardwareUnavailable
            BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED -> BiometricStatus.NoneEnrolled
            BiometricManager.BIOMETRIC_ERROR_SECURITY_UPDATE_REQUIRED ->
                BiometricStatus.SecurityUpdateRequired
            else -> BiometricStatus.Unsupported
        }
    }

    fun authenticate(
        activity: FragmentActivity,
        title: String,
        subtitle: String,
        negativeButtonText: String,
        onSuccess: (BiometricPrompt.AuthenticationResult) -> Unit,
        onError: (Int, CharSequence) -> Unit,
        onFailed: () -> Unit
    ) {
        val executor = ContextCompat.getMainExecutor(activity)

        val callback = object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                onSuccess(result)
            }

            override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                onError(errorCode, errString)
            }

            override fun onAuthenticationFailed() {
                onFailed()
            }
        }

        val prompt = BiometricPrompt(activity, executor, callback)

        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle(title)
            .setSubtitle(subtitle)
            .setNegativeButtonText(negativeButtonText)
            .setAllowedAuthenticators(
                Authenticators.BIOMETRIC_STRONG or Authenticators.BIOMETRIC_WEAK
            )
            .setConfirmationRequired(true)
            .build()

        prompt.authenticate(promptInfo)
    }

    fun authenticateWithCrypto(
        activity: FragmentActivity,
        cipher: Cipher,
        title: String,
        subtitle: String,
        negativeButtonText: String,
        onSuccess: (BiometricPrompt.AuthenticationResult) -> Unit,
        onError: (Int, CharSequence) -> Unit
    ) {
        val executor = ContextCompat.getMainExecutor(activity)

        val callback = object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                onSuccess(result)
            }

            override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                onError(errorCode, errString)
            }
        }

        val prompt = BiometricPrompt(activity, executor, callback)

        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle(title)
            .setSubtitle(subtitle)
            .setNegativeButtonText(negativeButtonText)
            .setAllowedAuthenticators(Authenticators.BIOMETRIC_STRONG)
            .build()

        prompt.authenticate(promptInfo, BiometricPrompt.CryptoObject(cipher))
    }
}

enum class BiometricStatus {
    Available,
    NoHardware,
    HardwareUnavailable,
    NoneEnrolled,
    SecurityUpdateRequired,
    Unsupported
}
```

### Using Biometrics in Compose

```kotlin
@Composable
fun BiometricLoginButton(
    onAuthenticated: () -> Unit,
    onError: (String) -> Unit
) {
    val context = LocalContext.current
    val activity = context as? FragmentActivity ?: return
    val authenticator = remember { BiometricAuthenticator() }

    val canAuthenticate = remember {
        authenticator.canAuthenticate(context)
    }

    if (canAuthenticate != BiometricStatus.Available) return

    Button(
        onClick = {
            authenticator.authenticate(
                activity = activity,
                title = context.getString(R.string.biometric_title),
                subtitle = context.getString(R.string.biometric_subtitle),
                negativeButtonText = context.getString(R.string.biometric_cancel),
                onSuccess = { onAuthenticated() },
                onError = { _, errString -> onError(errString.toString()) },
                onFailed = { onError("Authentication failed") }
            )
        }
    ) {
        Text(stringResource(R.string.login_with_biometrics))
    }
}
```

### Biometric + Keystore (Bank-Level Security)

For highest security, combine biometric auth with hardware-backed key:

```kotlin
class BiometricCryptoManager @Inject constructor(
    private val keystoreManager: KeystoreManager
) {
    private val keyAlias = "biometric_key"

    fun createBiometricKey() {
        keystoreManager.createKey(
            alias = keyAlias,
            requireBiometric = true,
            requireStrongBox = true
        )
    }

    fun getCipherForEncryption(): Cipher {
        val key = keystoreManager.createKey(
            alias = keyAlias,
            requireBiometric = true
        )
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key)
        return cipher
    }

    fun getCipherForDecryption(iv: ByteArray): Cipher {
        val keyStore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val key = (keyStore.getEntry(keyAlias, null) as KeyStore.SecretKeyEntry).secretKey
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(128, iv))
        return cipher
    }
}
```

## Credential Manager and Sign-In

**BiometricPrompt** (above) covers local biometric unlock. For **sign-in**, Google recommends **Credential Manager** (`androidx.credentials`) as the unified API for **passkeys**, saved passwords, and federated identity (for example Sign in with Google) in one user flow. It replaces older Smart Lock Password Manager integration patterns for new work.

- Use Credential Manager for new sign-in and account linking flows where it fits your backend (WebAuthn / passkeys require server support).
- Keep **server-side** validation authoritative; the client only collects credentials.
- See [Sign in your user with Credential Manager](https://developer.android.com/identity/sign-in/credential-manager) and [Passkeys](https://developer.android.com/identity/sign-in/passkeys).

## Device Identifiers and Privacy

Do **not** use hardware identifiers for advertising or routine analytics. Google Play policies restrict many identifiers; users expect resettable, transparent tracking.

| Identifier                                                              | Guidance                                                                                                                   |
|-------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| IMEI, IMSI, serial number, MAC address                                  | Do not use for ads or general analytics; restricted / disallowed for most use cases                                        |
| [Advertising ID](https://developer.android.com/training/articles/ad-id) | Use for ads and measurement where allowed; user can reset; declare in Play Data Safety                                     |
| **Android ID**                                                          | App-scoped on modern Android; may change after factory reset; use only when appropriate, not as a global cross-app user ID |
| App-specific ID                                                         | Generate and store a random UUID in app storage or tie identity to your **account** after sign-in                          |

Prefer **account-based** identity for personalization. For crash and product analytics without PII, follow `references/crashlytics.md` scrubbing rules.

## Play Console Data Safety

In Play Console, complete the **Data safety** section (what you collect, how it is used, whether it is optional, retention). It must match your **privacy policy** URL and in-app disclosures.

- Allow **account and data deletion** where required by policy and your product.
- If you use Advertising ID or sensitive permissions, declare them accurately; mismatches can cause policy violations.

See [Play Console Help - Data safety](https://support.google.com/googleplay/android-developer/answer/10787469) and [User Data policy](https://support.google.com/googleplay/android-developer/answer/10144311).

## Play Integrity API

Replaces SafetyNet Attestation API (deprecated). Verifies device integrity, app integrity, and licensing. Use **Standard** requests for most on-demand checks; reserve **Classic** for infrequent, high-value actions. Official docs: [Overview](https://developer.android.com/google/play/integrity/overview), [Setup](https://developer.android.com/google/play/integrity/setup), [Standard requests](https://developer.android.com/google/play/integrity/standard), [Classic requests](https://developer.android.com/google/play/integrity/classic).

### Prerequisites and project setup

**Steps 1-2 need a human with Google Cloud and Play Console access.** An AI cannot log into those consoles. When implementing Play Integrity in code, **ask the engineer** to complete enablement and linking first, then obtain the value(**numeric Cloud project number**) below so the client and backend can be wired correctly.

1. **Google Cloud (engineer):** Create or select a project; enable the **Play Integrity API** ([Setup guide](https://developer.android.com/google/play/integrity/setup)). The engineer should share the **Google Cloud project number** (numeric, shown in Cloud Console for the project). You pass it to `PrepareIntegrityTokenRequest.setCloudProjectNumber` (Standard API) and to Classic requests when the docs require it. Backend teams create a **service account** in this project with access to call the Play Integrity **decode** API (see [Google's server verification docs](https://developer.android.com/google/play/integrity/standard#decrypt-and-verify-the-integrity-verdict)); those credentials stay on the server.
2. **Play Console (engineer):** Link that Cloud project to your app under **Test and release** > **App integrity** > **Play Integrity API** > **Link a Cloud project**. Linking is required for quota increases, response configuration in Console, and related tooling. Projects enabled only in Cloud Console but not linked get a limited integration path per Google.
3. **Quotas (defaults):** Roughly **10,000** integrity token operations and **10,000** server-side decryptions per day for the linked Cloud project (shared across request types; see [Setup](https://developer.android.com/google/play/integrity/setup) for current numbers and how to request more).
4. **Dependency:** Add the Play Integrity library via your Gradle version catalog. In this skill, the template is [`assets/libs.versions.toml.template`](../assets/libs.versions.toml.template): use `version.ref = "playIntegrity"` and the library alias `play-integrity` (`com.google.android.play:integrity`). Mirror that pattern in your project's `gradle/libs.versions.toml` and module `build.gradle.kts` (see [Dependencies](#dependencies)).

### Standard API vs Classic API

|                                   | **Standard API**                                                                                                                                     | **Classic API**                                                                                                       |
|-----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| **Warm-up**                       | Yes - call `prepareIntegrityToken` before you need tokens (typical warm-up a few seconds; allow a generous timeout, e.g. on the order of one minute) | No                                                                                                                    |
| **Typical latency after warm-up** | Lower (often hundreds of ms for the token request)                                                                                                   | Higher (often a few seconds)                                                                                          |
| **Use when**                      | Frequent checks tied to user actions or API calls                                                                                                    | Rare, high-value or sensitive actions                                                                                 |
| **Client binding field**          | `requestHash` (digest of the protected request; max length per API)                                                                                  | `nonce` (server-chosen or derived; format per [Classic](https://developer.android.com/google/play/integrity/classic)) |
| **Replay / tamper mitigation**    | Google Play mitigates replay for Standard; still bind with `requestHash` for request integrity                                                       | You must implement nonce handling and server checks                                                                   |
| **Rate limits (documented)**      | Prepare: **5** warm-up calls per app instance per minute; token requests subject to product limits                                                   | **5** integrity token requests per app instance per minute for Classic                                                |

Library `minSdk` for both follows the Play Integrity library version you ship (see release notes for the exact floor).

### Standard API client flow

- Create `StandardIntegrityManager` via `IntegrityManagerFactory.createStandard(context)`.
- **Once per session (or after errors below):** call `prepareIntegrityToken` with `PrepareIntegrityTokenRequest` that sets your **Google Cloud project number**. Keep the resulting `StandardIntegrityTokenProvider` in memory.
- **On each protected action:** build a stable digest of the data you need to bind (for example SHA-256 of a canonical string of request fields), pass it as **`requestHash`** in `StandardIntegrityTokenRequest`. Do not put sensitive values in plaintext in the hash input; hash them.
- If you receive **`INTEGRITY_TOKEN_PROVIDER_INVALID`**, prepare a new provider and retry the token request.
- Optional: use **`verdictOptOut`** on a Standard request to skip optional verdicts that add latency when you do not need them (see API reference / release notes).

### Classic API client flow

- Use `IntegrityManagerFactory.create(context)` and `IntegrityTokenRequest` with a **`nonce`** meeting Google's format (Base64 URL-safe, no wrap, length limits in the docs).
- Apps **distributed through Google Play** usually do **not** need `setCloudProjectNumber` on the request because the app is linked in Play Console.
- Apps **not** installed from Play (or SDK integrations as documented) may need **`setCloudProjectNumber`** - follow [Classic requests](https://developer.android.com/google/play/integrity/classic).
- Use Classic **sparingly**; it is heavier and you own nonce and replay policy on the server.

### Policy (enforcement)

- **Do not** treat a decrypted verdict as a long-lived "device is trusted forever" flag in the client. Avoid caching integrity results to authorize unrelated later actions.
- Apply **tiered** server rules: allow, allow with limits, step-up (OTP, delay), or deny **only** the sensitive operation - avoid locking the whole app on the first failure unless product requires it.
- **Optional verdicts** (extra device labels, app access risk, Play Protect, recent device activity, device recall, etc.) require opting in under Play Console **App integrity** > **Play Integrity API** > **Settings** / **Change responses**. Only enforce signals you actually receive and have enabled.
- Roll out **telemetry first** (log or soft-fail), then tighten enforcement as you understand your user base.

### Setup

Add the Play Integrity dependency (see [Dependencies](#dependencies)). Call **`warmUp()`** once after launch (or in background) so the first protected action is not paying full prepare latency. Use **`requestIntegrityToken(requestHash)`** only with a digest built for that action (see [Standard API client flow](#standard-api-client-flow)).

```kotlin
// core/data/integrity/PlayIntegrityChecker.kt
import com.google.android.play.core.integrity.IntegrityManagerFactory
import com.google.android.play.core.integrity.StandardIntegrityManager
import kotlinx.coroutines.tasks.await

class PlayIntegrityChecker @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val integrityManager = IntegrityManagerFactory.createStandard(context)

    @Volatile
    private var tokenProvider: StandardIntegrityManager.StandardIntegrityTokenProvider? = null

    /** Call once (e.g. Application onCreate or before first sensitive call). */
    suspend fun warmUp(): Result<Unit> {
        if (tokenProvider != null) return Result.success(Unit)
        return try {
            tokenProvider = integrityManager
                .prepareIntegrityToken(
                    StandardIntegrityManager.PrepareIntegrityTokenRequest.builder()
                        .setCloudProjectNumber(YOUR_CLOUD_PROJECT_NUMBER)
                        .build()
                )
                .await()
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /** Request a token bound to this server action via requestHash (Standard API). */
    suspend fun requestIntegrityToken(requestHash: String): Result<String> {
        warmUp().getOrElse { return Result.failure(it) }
        return try {
            val request = StandardIntegrityManager.StandardIntegrityTokenRequest.builder()
                .setRequestHash(requestHash)
                .build()
            val tokenResponse = tokenProvider!!.request(request).await()
            Result.success(tokenResponse.token())
        } catch (e: Exception) {
            tokenProvider = null
            Result.failure(e)
        }
    }
}
```

### Server-Side Verification

**The integrity token must be verified server-side.** Never trust client-side validation alone. The backend calls Google's **`decodeIntegrityToken`** API with a service account (see [Decrypt and verify the integrity verdict](https://developer.android.com/google/play/integrity/standard#decrypt-and-verify-the-integrity-verdict)). Recompute **`requestHash`** the same way as the client and compare to **`requestDetails.requestHash`** in the decrypted payload.

```kotlin
// Send token + the same requestHash your server will recompute for verification
class IntegrityRepository @Inject constructor(
    private val api: IntegrityApi,
    private val integrityChecker: PlayIntegrityChecker
) {
    suspend fun verifyProtectedAction(requestHash: String): Result<IntegrityVerdict> {
        val token = integrityChecker.requestIntegrityToken(requestHash).getOrElse {
            return Result.failure(it)
        }
        return api.verifyIntegrity(token, requestHash)
    }
}
```

### Server decode and verify checklist

After your backend receives the integrity token string, call **`decodeIntegrityToken`** with a **service account** that has the **`playintegrity`** scope (see [Decrypt and verify the integrity verdict](https://developer.android.com/google/play/integrity/standard#decrypt-and-verify-the-integrity-verdict)). Validate the decrypted JSON **in order**:

1. **`requestDetails`** - `requestPackageName` equals your application ID. For Standard requests, **`requestHash`** equals the value you computed for this action (same algorithm and canonical serialization as the client). Check **`timestampMillis`** is within a window you allow (reject stale tokens). For Classic requests, compare **`nonce`** to the value you issued for this request.
2. **`appIntegrity`** - `appRecognitionVerdict` (for example `PLAY_RECOGNIZED` vs `UNRECOGNIZED_VERSION`).
3. **`deviceIntegrity`** - `deviceRecognitionVerdict` labels (for example `MEETS_DEVICE_INTEGRITY`, optional labels if you opted in under Play Console).
4. **`accountDetails`** - `appLicensingVerdict` (for example `LICENSED` vs `UNLICENSED`).
5. **`environmentDetails`** - Only present if you enabled optional verdicts in Play Console; interpret **app access risk** and **Play Protect** per [Integrity verdicts](https://developer.android.com/google/play/integrity/verdicts).

Repeated decryption of the **same** token can clear or weaken verdicts (Google documents replay protection). Issue one token per protected server request.

### Standard API sequence (reference)

```mermaid
sequenceDiagram
    participant App
    participant PlayServices as PlayIntegrity
    participant Backend
    participant GoogleAPI as GoogleDecode
    App->>PlayServices: prepareIntegrityToken
    PlayServices-->>App: StandardIntegrityTokenProvider
    App->>PlayServices: request with requestHash
    PlayServices-->>App: integrity token string
    App->>Backend: HTTPS with token
    Backend->>GoogleAPI: decodeIntegrityToken
    GoogleAPI-->>Backend: verdict JSON
```

### Client errors and retries

Use the official matrix: [Handle Play Integrity API error codes](https://developer.android.com/google/play/integrity/error-codes).

- **Often retry with backoff** (transient): `NETWORK_ERROR`, `TOO_MANY_REQUESTS`, `GOOGLE_SERVER_UNAVAILABLE`, `CLIENT_TRANSIENT_ERROR`, `INTERNAL_ERROR`; follow Google guidance (initial delay, exponential backoff, cap attempts).
- **Usually fix environment or config** (not a blind retry): `API_NOT_AVAILABLE`, `PLAY_STORE_NOT_FOUND`, `PLAY_STORE_VERSION_OUTDATED`, `PLAY_SERVICES_NOT_FOUND`, `PLAY_SERVICES_VERSION_OUTDATED`, `CLOUD_PROJECT_NUMBER_IS_INVALID`, `CANNOT_BIND_TO_SERVICE` - prompt user to update Play Store or Play services, or fix the Cloud project number you pass from the engineer.
- **Standard only:** `INTEGRITY_TOKEN_PROVIDER_INVALID` - **invalidate the cached provider**, clear it, run **`warmUp()`** again, then retry the token request.
- **`REQUEST_HASH_TOO_LONG`** - shorten the digest input or hash to a fixed-length string before sending.

Treat persistent failures after retries as **failed integrity** for that action and apply your tiered policy (do not assume success).

### Remediation dialogs

Google Play can show **in-app dialogs** so users fix licensing, Play services, or integrity issues. See [Remediation dialogs](https://developer.android.com/google/play/integrity/remediation). Requires Play Integrity library **1.3.0 or higher** for `showDialog` on token responses; **1.5.0 or higher** for `GET_INTEGRITY` / `GET_STRONG_INTEGRITY` style flows on **remediable** exceptions.

- **Your server** decides whether to ask the client to show a dialog (for example after a bad verdict or a specific error code).
- **Your app** builds `StandardIntegrityDialogRequest` (or the Classic equivalent) with the **activity**, dialog **type code**, and the **token or exception** payload from the API.
- After the user closes the dialog, **request a fresh token**; for Standard API, **prepare the token provider again** (warm up) before the next integrity request, as documented on the remediation page.

### Integrity Verdicts

| Verdict                   | Meaning                                              |
|---------------------------|------------------------------------------------------|
| `MEETS_DEVICE_INTEGRITY`  | Real device with Google Play                         |
| `MEETS_BASIC_INTEGRITY`   | Device may be rooted but passes basic checks         |
| `MEETS_STRONG_INTEGRITY`  | Genuine device, recent security patch, boot verified |
| `MEETS_VIRTUAL_INTEGRITY` | Running in an emulator recognized by Google Play     |

## Root & Emulator Detection

### How this fits next to Play Integrity

**For the AI implementing this skill:** Use **local root and emulator checks** below as **supplementary signals** (telemetry, fraud hints, optional warnings, or feature gating). They are **easy to miss or hide** on modified devices and must **not** be your only line of defense for **API authorization** or **high-value actions** when you can use **Play Integrity** instead.

- Prefer **server-verified** integrity tokens and **backend policy** for login, payments, and sensitive operations (see [Modern device trust and abuse resistance](#modern-device-trust-and-abuse-resistance) and [Play Integrity API](#play-integrity-api)).
- If you ship both, **do not** treat "root detected" as equivalent to "Play Integrity failed"; align UX and logs with your **tiered** rules.
- Official context: [Play Integrity API overview](https://developer.android.com/google/play/integrity/overview).

### Root Detection

```kotlin
// core/data/security/RootDetector.kt
class RootDetector @Inject constructor() {

    fun isDeviceRooted(): Boolean {
        return checkRootBinaries() ||
            checkSuExists() ||
            checkRootProperties() ||
            checkRootCloaking() ||
            checkTestKeys()
    }

    private fun checkRootBinaries(): Boolean {
        val paths = listOf(
            "/system/bin/su", "/system/xbin/su", "/sbin/su",
            "/data/local/xbin/su", "/data/local/bin/su",
            "/system/sd/xbin/su", "/system/bin/failsafe/su",
            "/data/local/su", "/su/bin/su",
            "/system/app/Superuser.apk",
            "/system/app/SuperSU.apk",
            "/system/app/Kinguser.apk",
            // Magisk
            "/sbin/.magisk", "/cache/.disable_magisk",
            "/dev/.magisk/mirror",
        )
        return paths.any { File(it).exists() }
    }

    private fun checkSuExists(): Boolean {
        return try {
            Runtime.getRuntime().exec("which su")
                .inputStream.bufferedReader().readLine() != null
        } catch (_: Exception) {
            false
        }
    }

    private fun checkRootProperties(): Boolean {
        val dangerousProps = mapOf(
            "ro.debuggable" to "1",
            "ro.secure" to "0"
        )
        return dangerousProps.any { (key, value) ->
            try {
                val process = Runtime.getRuntime().exec("getprop $key")
                val result = process.inputStream.bufferedReader().readLine()?.trim()
                result == value
            } catch (_: Exception) {
                false
            }
        }
    }

    private fun checkRootCloaking(): Boolean {
        val cloakingPackages = listOf(
            "com.devadvance.rootcloak",
            "com.devadvance.rootcloakplus",
            "de.robv.android.xposed.installer",
            "com.saurik.substrate",
            "com.zachspong.temprootremovejb",
            "com.amphoras.hidemyroot",
            "com.koushikdutta.superuser",
            "eu.chainfire.supersu",
            "com.topjohnwu.magisk"
        )
        return cloakingPackages.any { pkg ->
            try {
                Runtime.getRuntime().exec("pm list packages $pkg")
                    .inputStream.bufferedReader().readLine()?.contains(pkg) == true
            } catch (_: Exception) {
                false
            }
        }
    }

    private fun checkTestKeys(): Boolean {
        val buildTags = Build.TAGS
        return buildTags != null && buildTags.contains("test-keys")
    }
}
```

### Emulator Detection

```kotlin
// core/data/security/EmulatorDetector.kt
class EmulatorDetector @Inject constructor() {

    fun isEmulator(): Boolean {
        return checkBuildProperties() ||
            checkHardware() ||
            checkSensors()
    }

    private fun checkBuildProperties(): Boolean {
        return (Build.FINGERPRINT.startsWith("generic") ||
            Build.FINGERPRINT.startsWith("unknown") ||
            Build.MODEL.contains("google_sdk") ||
            Build.MODEL.lowercase().contains("droid4x") ||
            Build.MODEL.contains("Emulator") ||
            Build.MODEL.contains("Android SDK built for") ||
            Build.MANUFACTURER.contains("Genymotion") ||
            Build.HARDWARE.contains("goldfish") ||
            Build.HARDWARE.contains("ranchu") ||
            Build.HARDWARE.contains("vbox86") ||
            Build.PRODUCT.contains("sdk") ||
            Build.PRODUCT.contains("vbox86p") ||
            Build.PRODUCT.contains("emulator") ||
            Build.PRODUCT.contains("simulator") ||
            Build.BOARD.lowercase().contains("nox") ||
            Build.BOOTLOADER.lowercase().contains("nox") ||
            Build.HARDWARE.lowercase().contains("nox") ||
            Build.PRODUCT.lowercase().contains("nox") ||
            Build.SERIAL.lowercase().contains("nox"))
    }

    private fun checkHardware(): Boolean {
        return try {
            val cpuInfo = File("/proc/cpuinfo").readText()
            cpuInfo.contains("hypervisor") ||
                cpuInfo.contains("QEMU") ||
                cpuInfo.contains("Goldfish")
        } catch (_: Exception) {
            false
        }
    }

    private fun checkSensors(): Boolean {
        // Emulators typically have 0 or very few sensors
        return try {
            val sensorManager = android.hardware.SensorManager::class.java
            false // Requires context; implement via DI
        } catch (_: Exception) {
            false
        }
    }
}
```

### Architecture Integration

```kotlin
// core/data/security/SecurityChecker.kt
class SecurityChecker @Inject constructor(
    private val rootDetector: RootDetector,
    private val emulatorDetector: EmulatorDetector,
    private val integrityChecker: PlayIntegrityChecker,
    private val crashReporter: CrashReporter
) {
    data class SecurityReport(
        val isRooted: Boolean,
        val isEmulator: Boolean,
        val integrityVerdict: IntegrityVerdict? = null
    )

    suspend fun performSecurityCheck(): SecurityReport {
        val isRooted = rootDetector.isDeviceRooted()
        val isEmulator = emulatorDetector.isEmulator()

        if (isRooted) {
            crashReporter.log("Security: Rooted device detected")
        }
        if (isEmulator) {
            crashReporter.log("Security: Emulator detected")
        }

        return SecurityReport(
            isRooted = isRooted,
            isEmulator = isEmulator
        )
    }
}
```

### Handling Detection Results

Don't crash or block users without good reason. Choose a response based on your app's risk level:

| Risk Level              | Rooted Device          | Emulator            |
|-------------------------|------------------------|---------------------|
| **Low** (news app)      | Log warning            | Allow               |
| **Medium** (e-commerce) | Show warning, log      | Block in production |
| **High** (banking)      | Block with explanation | Block               |

```kotlin
@HiltViewModel
class SecurityViewModel @Inject constructor(
    private val securityChecker: SecurityChecker
) : ViewModel() {

    private val _securityState = MutableStateFlow<SecurityState>(SecurityState.Checking)
    val securityState: StateFlow<SecurityState> = _securityState.asStateFlow()

    init {
        viewModelScope.launch {
            val report = securityChecker.performSecurityCheck()
            _securityState.value = when {
                report.isRooted -> SecurityState.RootedDevice
                report.isEmulator && !BuildConfig.DEBUG -> SecurityState.EmulatorDetected
                else -> SecurityState.Secure
            }
        }
    }
}
```

## Screenshot & Screen Recording Prevention

### Prevent Screenshots (FLAG_SECURE)

```kotlin
// In Activity
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Prevent screenshots and screen recording
        if (!BuildConfig.DEBUG) {
            window.setFlags(
                WindowManager.LayoutParams.FLAG_SECURE,
                WindowManager.LayoutParams.FLAG_SECURE
            )
        }
    }
}
```

### Per-Screen Screenshot Prevention in Compose

For more granular control (e.g., only block on sensitive screens):

```kotlin
@Composable
fun SecureScreen(content: @Composable () -> Unit) {
    val activity = LocalContext.current as? Activity

    DisposableEffect(Unit) {
        activity?.window?.setFlags(
            WindowManager.LayoutParams.FLAG_SECURE,
            WindowManager.LayoutParams.FLAG_SECURE
        )
        onDispose {
            activity?.window?.clearFlags(WindowManager.LayoutParams.FLAG_SECURE)
        }
    }

    content()
}

// Usage
@Composable
fun PaymentScreen() {
    SecureScreen {
        Column {
            Text("Enter card details")
            // Payment form
        }
    }
}
```

### Preventing Recent Apps Thumbnail

`FLAG_SECURE` also prevents the app from appearing in the recent apps screenshot.

## Secure Database (Room 3)

Room 3 requires a [`SQLiteDriver`](https://developer.android.com/kotlin/multiplatform/sqlite#sqlite-driver) on [`Room.databaseBuilder`](https://developer.android.com/jetpack/androidx/releases/room3). It does **not** support `SupportSQLiteOpenHelper.Factory` or `openHelperFactory` (removed with SupportSQLite).

### Building the database (driver required)

```kotlin
// core/database/di/DatabaseModule.kt
import android.content.Context
import androidx.room3.Room
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder<AppDatabase>(
            context = context,
            name = "app_database",
        )
            .setDriver(BundledSQLiteDriver())
            .fallbackToDestructiveMigration()
            .build()
    }
}
```

`BundledSQLiteDriver` matches the `sqlite-bundled` dependency added by the `app.android.room` convention (see `assets/libs.versions.toml.template`).

### SQLCipher / full-database encryption

The Room 2 pattern `SupportOpenHelperFactory` + `openHelperFactory` does **not** apply to Room 3. To encrypt the whole database, follow **SQLCipher** (or your vendor) documentation for an **`SQLiteDriver`** (or supported integration) compatible with **`androidx.sqlite`**, then pass it to `.setDriver(...)`. The [`room3-sqlite-wrapper`](https://developer.android.com/jetpack/androidx/releases/room3) artifact is for bridging **legacy `SupportSQLite` call sites**, not for replacing a proper driver on the main `RoomDatabase` builder. See [Migrate from SupportSQLite](https://developer.android.com/kotlin/multiplatform/room#migrate) and [Room 3 release notes](https://developer.android.com/jetpack/androidx/releases/room3).

### Sensitive Field Encryption

For encrypting specific fields (when full-database encryption is too heavy):

```kotlin
import androidx.room3.ColumnInfo
import androidx.room3.Entity
import androidx.room3.PrimaryKey

@Entity(tableName = "users")
data class UserEntity(
    @PrimaryKey val id: String,
    val name: String,
    @ColumnInfo(name = "encrypted_ssn")
    val encryptedSsn: ByteArray,  // Encrypted with AES-GCM
    @ColumnInfo(name = "ssn_iv")
    val ssnIv: ByteArray  // IV for decryption
)

// Repository handles encryption/decryption
class UserRepositoryImpl @Inject constructor(
    private val userDao: UserDao,
    private val encryption: AesGcmEncryption
) : UserRepository {
    private val key = encryption.getOrCreateKey("user_data_key")

    override suspend fun saveUser(user: User) {
        val encrypted = encryption.encrypt(user.ssn.toByteArray(), key)
        val iv = encrypted.copyOfRange(0, 12)
        val ciphertext = encrypted.copyOfRange(12, encrypted.size)

        userDao.insert(UserEntity(
            id = user.id,
            name = user.name,
            encryptedSsn = ciphertext,
            ssnIv = iv
        ))
    }
}
```

## Secure Clipboard

### Prevent Clipboard Leaks

```kotlin
// For sensitive fields, set clipboard to expire
@Composable
fun SensitiveTextField(
    value: String,
    onValueChange: (String) -> Unit
) {
    val clipboardManager = LocalClipboardManager.current

    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        visualTransformation = PasswordVisualTransformation(),
        keyboardOptions = KeyboardOptions(
            keyboardType = KeyboardType.Password,
            imeAction = ImeAction.Done,
            autoCorrectEnabled = false
        )
    )
}
```

### Android 13+ Clipboard Auto-Clear

On Android 13+ (API 33), sensitive clipboard content is automatically cleared after a timeout. For older versions, flag the content:

```kotlin
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
    val clipData = ClipData.newPlainText("", sensitiveText)
    val clipDescription = clipData.description
    val extras = PersistableBundle().apply {
        putBoolean(ClipDescription.EXTRA_IS_SENSITIVE, true)
    }
    clipDescription.extras = extras
    clipboardManager.setPrimaryClip(clipData)
}
```

## WebView Security

### Secure WebView Configuration

```kotlin
@Composable
fun SecureWebView(url: String) {
    AndroidView(
        factory = { context ->
            WebView(context).apply {
                settings.apply {
                    javaScriptEnabled = false // Enable only if needed
                    allowFileAccess = false
                    allowContentAccess = false
                    domStorageEnabled = false
                    setSupportMultipleWindows(false)
                    javaScriptCanOpenWindowsAutomatically = false

                    // Disable geolocation
                    setGeolocationEnabled(false)

                    // Disable mixed content
                    mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW

                    // Disable cache for sensitive content
                    cacheMode = WebSettings.LOAD_NO_CACHE
                }

                webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(
                        view: WebView?,
                        request: WebResourceRequest?
                    ): Boolean {
                        val requestUrl = request?.url?.toString() ?: return true
                        // Only allow your domain
                        return !requestUrl.startsWith("https://yourdomain.com")
                    }
                }
            }
        },
        update = { webView -> webView.loadUrl(url) }
    )
}
```

### Avoid `addJavascriptInterface` Attack Surface

If JavaScript must be enabled, avoid `addJavascriptInterface()` as it exposes your app to XSS attacks. Use `evaluateJavascript()` for controlled communication instead.

## Content Provider Security

### Restrict Content Provider Access

```xml
<!-- AndroidManifest.xml -->
<provider
    android:name=".data.provider.AppContentProvider"
    android:authorities="${applicationId}.provider"
    android:exported="false"
    android:grantUriPermissions="false" />
```

### FileProvider for Secure File Sharing

```xml
<provider
    android:name="androidx.core.content.FileProvider"
    android:authorities="${applicationId}.fileprovider"
    android:exported="false"
    android:grantUriPermissions="true">
    <meta-data
        android:name="android.support.FILE_PROVIDER_PATHS"
        android:resource="@xml/file_paths" />
</provider>
```

```xml
<!-- res/xml/file_paths.xml -->
<paths>
    <files-path name="internal_files" path="." />
    <cache-path name="cache" path="." />
</paths>
```

## ProGuard / R8 Hardening

Use `assets/proguard-rules.pro.template` as the source of truth for all keep rules. It includes security-specific sections:

- **Log stripping** - removes `Log.v/d/i/w` calls in release builds
- **Crypto/security class preservation** - keeps `core.data.crypto.**` and `core.data.security.**`
- **Obfuscation hardening** - `repackageclasses`, `allowaccessmodification`
- **Crash report readability** - `SourceFile,LineNumberTable` attributes preserved
- **Mapping file upload** - Firebase and Sentry Gradle plugins handle this automatically

See [gradle-setup.md](gradle-setup.md#r8--proguard-configuration) for build configuration and debugging shrunk builds.

### Manifest Security

```xml
<application
    android:allowBackup="false"
    android:fullBackupContent="false"
    android:dataExtractionRules="@xml/data_extraction_rules"
    android:networkSecurityConfig="@xml/network_security_config"
    android:usesCleartextTraffic="false"
    ... >

    <!-- Prevent other apps from reading your activities -->
    <activity
        android:name=".MainActivity"
        android:exported="true">
        <!-- Only this activity is exported (launcher) -->
    </activity>

    <!-- All other activities should NOT be exported -->
    <activity
        android:name=".PaymentActivity"
        android:exported="false" />
</application>
```

### Data Extraction Rules (API 31+)

```xml
<!-- res/xml/data_extraction_rules.xml -->
<data-extraction-rules>
    <cloud-backup>
        <exclude domain="sharedpref" path="secure_prefs.xml" />
        <exclude domain="database" path="app_database" />
        <exclude domain="file" path="." />
    </cloud-backup>
    <device-transfer>
        <exclude domain="sharedpref" path="secure_prefs.xml" />
        <exclude domain="database" path="app_database" />
    </device-transfer>
</data-extraction-rules>
```

## CI/CD Security

### Secrets Management

```yaml
# .github/workflows/build.yml
env:
  KEYSTORE_FILE: ${{ secrets.KEYSTORE_FILE }}
  KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
  KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
  KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}
```

**Never commit:**
- `*.jks` or `*.keystore` files
- `google-services.json` with production keys
- `sentry.properties` with auth tokens
- Any `.env` files
- API keys in source code

### .gitignore Entries

```gitignore
# Signing
*.jks
*.keystore
signing.properties

# API keys
google-services.json
sentry.properties
local.properties

# Build artifacts
/build/
*.apk
*.aab
```

### Static Analysis in CI

```yaml
# .github/workflows/security.yml
name: Security Checks

on: [pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for hardcoded secrets
        run: |
          if grep -rn "AIza\|sk_live\|-----BEGIN" --include="*.kt" --include="*.xml" app/; then
            echo "Potential secrets found in source code!"
            exit 1
          fi

      - name: Run Detekt security rules
        run: ./gradlew detekt

      - name: Check dependencies for vulnerabilities
        run: ./gradlew dependencyCheckAnalyze
```

## Security Checklist

Use this checklist for every release:

### Network
- [ ] HTTPS enforced for all endpoints
- [ ] Certificate pinning configured for critical APIs
- [ ] Network security config blocks cleartext traffic
- [ ] TLS 1.2+ enforced

### Data at Rest
- [ ] Auth tokens in `EncryptedSharedPreferences`
- [ ] Sensitive database fields encrypted (or full SQLCipher)
- [ ] No sensitive data in logs (`Log.d`, etc.)
- [ ] Cloud backup excludes sensitive data (`data_extraction_rules.xml`)
- [ ] `android:allowBackup="false"` in manifest

### Authentication
- [ ] BiometricPrompt for sensitive actions
- [ ] Credential Manager / passkeys or other sign-in flows aligned with backend (where applicable)
- [ ] No hardware IDs (IMEI, MAC, serial) used for tracking; Advertising ID only where policy allows
- [ ] Session timeout implemented
- [ ] Re-authentication for critical operations (payment, password change)

### Privacy and Play policy
- [ ] Play Console **Data safety** form matches actual SDK and app behavior
- [ ] Privacy policy URL current and linked from store listing / in-app as required
- [ ] User data deletion or export path documented where required

### App Hardening
- [ ] R8/ProGuard enabled for release builds
- [ ] Log stripping in release builds
- [ ] High-risk apps: local root/emulator checks only as **supplement** (telemetry or soft warnings); **do not** rely on them alone for protecting APIs if Play Integrity is available
- [ ] `FLAG_SECURE` on sensitive screens
- [ ] All activities `android:exported="false"` except launcher
- [ ] Content providers not exported unless needed
- [ ] WebView JavaScript disabled unless required

### Build & Deploy
- [ ] Signing keys not in version control
- [ ] API keys not hardcoded
- [ ] ProGuard mapping files uploaded to crash reporter
- [ ] Dependency vulnerability scanning in CI

### Device Security
- [ ] Play Integrity for high-risk apps: **linked Cloud project** in Play Console; **Cloud project number** in app config; **`warmUp()`** before first sensitive use where applicable
- [ ] **Standard** API: **`requestHash`** binding; **Classic** API: **`nonce`** per Google rules; server calls **`decodeIntegrityToken`** and validates **`requestDetails`** before other verdicts
- [ ] **Tiered** enforcement and **gradual** rollout (telemetry before hard blocks); **remediation** path for recoverable integrity failures where product allows
- [ ] Keystore-backed key generation for device-bound or high-value crypto where designed
- [ ] StrongBox used when available

## Best Practices Summary

1. **Defense in depth**: Layer multiple security controls
2. **Least privilege**: Request only necessary permissions
3. **Fail securely**: Default to denying access on errors
4. **Don't trust the client**: All critical validation must happen server-side
5. **Encrypt everything sensitive**: At rest and in transit
6. **Keep dependencies updated**: Monitor for CVEs
7. **Test security**: Include security tests in CI/CD
8. **Log security events**: But never log sensitive data
9. **Use hardware security**: Keystore > software encryption
10. **High-value actions**: Prefer **Play Integrity** with server decode, **`requestHash`** or **`nonce`** binding, and **tiered** backend policy; local root checks stay **supplementary**
11. **Follow Google's guidance**: [Android Security Tips](https://developer.android.com/privacy-and-security/security-tips)

## Related Guides

- [Crash Reporting](crashlytics.md) - CrashReporter interface and PII scrubbing
- [Permissions Guide](android-permissions.md) - Runtime permission patterns
- [Network Configuration](gradle-setup.md) - Network security config setup
- [Architecture Guide](architecture.md) - Repository patterns for secure data access
- [Data Sync Guide](android-data-sync.md) - Offline-first with encrypted local storage
- [StrictMode Guide](android-strictmode.md) - Detecting cleartext traffic
