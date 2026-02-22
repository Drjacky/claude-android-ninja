# Android Security

Security guide for Android apps, aligned with our modular architecture.

## Table of Contents
1. [Network Security](#network-security)
2. [Certificate Pinning](#certificate-pinning)
3. [Data Encryption at Rest](#data-encryption-at-rest)
4. [Android Keystore, TEE & StrongBox](#android-keystore-tee--strongbox)
5. [Biometric Authentication](#biometric-authentication)
6. [Play Integrity API](#play-integrity-api)
7. [Root & Emulator Detection](#root--emulator-detection)
8. [Screenshot & Screen Recording Prevention](#screenshot--screen-recording-prevention)
9. [Secure Database (Room)](#secure-database-room)
10. [Secure Clipboard](#secure-clipboard)
11. [WebView Security](#webview-security)
12. [Content Provider Security](#content-provider-security)
13. [ProGuard / R8 Hardening](#proguard--r8-hardening)
14. [CI/CD Security](#cicd-security)
15. [Security Checklist](#security-checklist)

## Dependencies

Security-related libraries available in the version catalog:

- `androidx-biometric` - BiometricPrompt (fingerprint, face)
- `androidx-security-crypto` - EncryptedSharedPreferences, EncryptedFile
- `play-integrity` - Play Integrity API (device/app attestation)
- `sqlcipher-android` - SQLCipher for encrypted Room databases

Add them to your module as needed, following [dependencies.md → Adding a New Dependency](dependencies.md#adding-a-new-dependency).

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

## Play Integrity API

Replaces SafetyNet Attestation API (deprecated). Verifies device integrity, app integrity, and licensing.

### Setup

Add the Play Integrity dependency (see [Dependencies](#dependencies)).

```kotlin
// core/data/integrity/PlayIntegrityChecker.kt
import com.google.android.play.core.integrity.IntegrityManagerFactory
import com.google.android.play.core.integrity.StandardIntegrityManager

class PlayIntegrityChecker @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val integrityManager = IntegrityManagerFactory.createStandard(context)

    suspend fun requestIntegrityToken(requestHash: String): Result<String> {
        return try {
            val request = StandardIntegrityManager.StandardIntegrityTokenRequest.builder()
                .setRequestHash(requestHash)
                .build()

            val response = integrityManager
                .prepareIntegrityToken(
                    StandardIntegrityManager.PrepareIntegrityTokenRequest.builder()
                        .setCloudProjectNumber(YOUR_CLOUD_PROJECT_NUMBER)
                        .build()
                )
                .await()

            val tokenResponse = response
                .request(request)
                .await()

            Result.success(tokenResponse.token())
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

### Server-Side Verification

**The integrity token must be verified server-side.** Never trust client-side validation alone.

```kotlin
// Send token to your backend
class IntegrityRepository @Inject constructor(
    private val api: IntegrityApi,
    private val integrityChecker: PlayIntegrityChecker
) {
    suspend fun verifyDeviceIntegrity(): Result<IntegrityVerdict> {
        val nonce = generateSecureNonce()
        val token = integrityChecker.requestIntegrityToken(nonce).getOrElse {
            return Result.failure(it)
        }

        // Server decrypts and verifies the token
        return api.verifyIntegrity(token, nonce)
    }

    private fun generateSecureNonce(): String {
        val bytes = ByteArray(32)
        java.security.SecureRandom().nextBytes(bytes)
        return Base64.encodeToString(bytes, Base64.NO_WRAP)
    }
}
```

### Integrity Verdicts

| Verdict                   | Meaning                                              |
|---------------------------|------------------------------------------------------|
| `MEETS_DEVICE_INTEGRITY`  | Real device with Google Play                         |
| `MEETS_BASIC_INTEGRITY`   | Device may be rooted but passes basic checks         |
| `MEETS_STRONG_INTEGRITY`  | Genuine device, recent security patch, boot verified |
| `MEETS_VIRTUAL_INTEGRITY` | Running in an emulator recognized by Google Play     |

## Root & Emulator Detection

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

## Secure Database (Room)

### SQLCipher Integration

For encrypting the entire Room database:

```kotlin
// core/database/di/DatabaseModule.kt
import net.zetetic.database.sqlcipher.SupportOpenHelperFactory

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(
        @ApplicationContext context: Context,
        securePreferences: SecurePreferences
    ): AppDatabase {
        val passphrase = getOrCreatePassphrase(securePreferences)
        val factory = SupportOpenHelperFactory(passphrase)

        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "app_database"
        )
            .openHelperFactory(factory)
            .fallbackToDestructiveMigration()
            .build()
    }

    private fun getOrCreatePassphrase(securePreferences: SecurePreferences): ByteArray {
        val existing = securePreferences.getDatabasePassphrase()
        if (existing != null) return existing

        val passphrase = ByteArray(32).also {
            java.security.SecureRandom().nextBytes(it)
        }
        securePreferences.saveDatabasePassphrase(passphrase)
        return passphrase
    }
}
```

### Sensitive Field Encryption

For encrypting specific fields (when full-database encryption is too heavy):

```kotlin
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

Use `templates/proguard-rules.pro.template` as the source of truth for all keep rules. It includes security-specific sections:

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
- [ ] Session timeout implemented
- [ ] Re-authentication for critical operations (payment, password change)

### App Hardening
- [ ] R8/ProGuard enabled for release builds
- [ ] Log stripping in release builds
- [ ] Root detection for high-risk apps
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
- [ ] Play Integrity API integration (for high-risk apps)
- [ ] Keystore-backed key generation
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
10. **Follow Google's guidance**: [Android Security Tips](https://developer.android.com/privacy-and-security/security-tips)

## Related Guides

- [Crash Reporting](crashlytics.md) - CrashReporter interface and PII scrubbing
- [Permissions Guide](android-permissions.md) - Runtime permission patterns
- [Network Configuration](gradle-setup.md) - Network security config setup
- [Architecture Guide](architecture.md) - Repository patterns for secure data access
- [Data Sync Guide](android-data-sync.md) - Offline-first with encrypted local storage
- [StrictMode Guide](android-strictmode.md) - Detecting cleartext traffic
