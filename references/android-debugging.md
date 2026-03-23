# Android Debugging

## Table of Contents

1. [Logcat](#logcat)
2. [ANR Debugging](#anr-debugging)
3. [Memory Leaks](#memory-leaks)
4. [R8 Stack Trace De-obfuscation](#r8-stack-trace-de-obfuscation)
5. [Gradle Build Failures](#gradle-build-failures)
6. [Compose Recomposition Debugging](#compose-recomposition-debugging)
7. [Multi-Layer Boundary Debugging](#multi-layer-boundary-debugging)
8. [ADB Quick Reference](#adb-quick-reference)

## Logcat

### Filtering by App

```bash
# Stream logs filtered by app package
adb logcat --pid=$(adb shell pidof -s com.example.app)

# Filter by tag and level
adb logcat -s "YourTag:E"

# Save full logcat to file for analysis
adb logcat -d > crash_log.txt
```

Log levels: `V` (verbose), `D` (debug), `I` (info), `W` (warn), `E` (error), `F` (fatal).

### When to use each level (operational discipline)

Use `android.util.Log` consistently so production and debug logs stay readable:

| Level   | Use for                                                                               |
|---------|---------------------------------------------------------------------------------------|
| `Log.i` | Normal checkpoints (feature started, important parameters that are not PII)           |
| `Log.w` | Recoverable problems (fallback used, retry, unexpected but handled state)             |
| `Log.e` | Failures (request failed, uncaught path in a catch that you log before mapping to UI) |

Avoid `Log.v`/`Log.d` spam in hot paths in release builds. Never log secrets, tokens, or personal data (see `references/android-security.md`).

### Reading Crash Logs

The root cause is usually at the bottom of the `Caused by:` chain, not the top-level exception.
Always read the full stack trace before forming a hypothesis.

## ANR Debugging

ANRs occur when Android's system watchdog decides the main thread (or a bounded callback path) did not respond in time. The timeout depends on **what** was blocked:

| Scenario                                      | Typical timeout                                    |
|-----------------------------------------------|----------------------------------------------------|
| Input dispatch (touch, key) on main           | ~5 seconds                                         |
| `BroadcastReceiver.onReceive` running on main | ~10 seconds                                        |
| Starting a service on main / bound work       | on the order of ~20 seconds for some service paths |

The **~5 second** rule is the one you hit most often from heavy work on the main thread.

### Gathering Evidence

```bash
# Pull ANR trace from device
adb pull /data/anr/traces.txt ./anr_traces.txt

# Stream while reproducing
adb logcat -s "ActivityManager:E" | grep -A 30 "ANR in"
```

### What to Look For

In the trace file, find the `main` thread and check its state:

- `MONITOR` - waiting for a lock held by another thread (deadlock candidate)
- `TIMED_WAITING` on `sleep` - something called `Thread.sleep()` on main
- Blocking I/O calls - database queries, network calls, file reads on main thread

### Common Causes

- Database or network call on the main thread
- `runBlocking` on the main thread
- Deadlock between coroutine scopes
- Expensive computation (JSON parsing, bitmap decoding) on main thread

## Memory Leaks

### Common Causes

1. **Static References to Context**: Storing an `Activity` context statically prevents the entire activity (and its view hierarchy) from being garbage collected. If you must use a static context, use the Application context.
2. **Inner Classes Holding Activity References**: Non-static inner classes implicitly hold a reference to their outer `Activity`. If doing background work, use a static inner class with a `WeakReference<Activity>`, or prefer Kotlin Coroutines tied to `lifecycleScope`.
3. **Handler Memory Leaks**: A `Handler` processing delayed messages can keep the `Activity` alive after it's destroyed. Always call `handler.removeCallbacksAndMessages(null)` in `onDestroy()`.

### LeakCanary

**Android Studio Panda 3+** includes a built-in LeakCanary integration in the Profiler
(a dedicated "Analyze Leaks" task). If you are on Panda 3 or newer, no dependency is needed -
use the Profiler task directly. See the
[Android Studio Panda 3 release notes](https://developer.android.com/studio/preview/features#leakcanary).

For older Android Studio versions, add the dependency to `debugImplementation` only:

```kotlin
debugImplementation(libs.leakcanary)
```

LeakCanary surfaces leak traces automatically via a notification. Read the trace top-to-bottom:
the first bold entry is the leaking object, and the path shows what holds the reference. Fix by
clearing the reference in the appropriate lifecycle callback.

### Manual Heap Dump

```bash
adb shell am dumpheap com.example.app /data/local/tmp/heap.hprof
adb pull /data/local/tmp/heap.hprof ./heap.hprof
```

Open the `.hprof` file in Android Studio's Memory Profiler for analysis.

## R8 Stack Trace De-obfuscation

R8 (the default code shrinker/obfuscator in AGP) renames classes, methods, and fields in release
builds. Crash stack traces from production are obfuscated and unreadable without the mapping file.

For R8 build configuration and keep rules, see [gradle-setup.md](gradle-setup.md#r8--proguard-configuration).

### R8 Output Files

After a release build (`./gradlew assembleRelease`), R8 produces these files in
`app/build/outputs/mapping/<variant>/`:

| File                | Purpose                                                       |
|---------------------|---------------------------------------------------------------|
| `mapping.txt`       | Maps obfuscated names back to original names                  |
| `usage.txt`         | Lists classes and members that were removed (tree-shaken)     |
| `seeds.txt`         | Lists classes and members matched by `-keep` rules (retained) |
| `configuration.txt` | The merged R8 configuration from all sources                  |

**Always archive `mapping.txt` alongside every release build.** Without it, production crash
traces cannot be decoded. Crashlytics and Sentry Gradle plugins upload this automatically.

### Using retrace (Automated)

```bash
# AGP retrace task
./gradlew :app:retrace --stacktrace-file crash.txt

# Or use the retrace CLI directly with the mapping file
retrace mapping.txt crash.txt

# retrace is bundled with Android SDK command-line tools:
# $ANDROID_HOME/cmdline-tools/latest/bin/retrace
```

### Manual De-obfuscation

When `retrace` is not available or you need to decode a partial trace manually, read `mapping.txt`
directly.

#### Mapping File Format

Each line maps an original name to its obfuscated name:

```
com.example.app.data.UserRepository -> a.b.c:
    java.lang.String userId -> a
    void fetchUser(java.lang.String) -> b
    1:3:void fetchUser(java.lang.String):42:44 -> b
```

Format:
- `original.ClassName -> obfuscated.Name:` - class mapping
- `    originalType fieldName -> obfuscatedName` - field mapping (indented)
- `    returnType methodName(params) -> obfuscatedName` - method mapping (indented)
- `    startLine:endLine:returnType methodName(params):originalStart:originalEnd -> obfuscatedName` - line number mapping

#### Step-by-Step Manual Decode

Given an obfuscated crash:

```
java.lang.NullPointerException
    at a.b.c.b(SourceFile:2)
    at d.e.a(SourceFile:5)
```

1. **Find the class**: Search `mapping.txt` for `-> a.b.c:` to find the original class name
2. **Find the method**: Under that class entry, search for `-> b` to find the original method
3. **Find the line**: Match the obfuscated line number (`2`) against the line mapping range (`1:3:...:42:44`) to compute the original line: `originalStart + (obfuscatedLine - startLine)` = `42 + (2 - 1)` = line `43`
4. Repeat for each frame in the stack trace

#### Example Walkthrough

Obfuscated trace:

```
Fatal Exception: java.lang.IllegalStateException: User not found
    at a.b.c.b(SourceFile:2)
```

Mapping entry:

```
com.example.app.data.UserRepository -> a.b.c:
    1:3:com.example.app.domain.User fetchUser(java.lang.String):42:44 -> b
```

Decoded:
- Class `a.b.c` = `com.example.app.data.UserRepository`
- Method `b` at line `2` = `fetchUser(String)` at original line `43` (42 + (2 - 1))

Result:

```
Fatal Exception: java.lang.IllegalStateException: User not found
    at com.example.app.data.UserRepository.fetchUser(UserRepository.kt:43)
```

### Debugging Unexpected Removal

If a class or method is unexpectedly removed or renamed by R8:

```bash
# Check what was removed
grep "ClassName" app/build/outputs/mapping/release/usage.txt

# Check what was kept
grep "ClassName" app/build/outputs/mapping/release/seeds.txt
```

If the class appears in `usage.txt`, add a `-keep` rule in `proguard-rules.pro`. If it appears in
neither file, it was likely not included in any dependency.

## Gradle Build Failures

Read Gradle errors from the **bottom up** - Gradle wraps errors in multiple layers.

### Common Error Patterns

| Error                     | Investigation                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------|
| `Manifest merger failed`  | Check `app/build/intermediates/merged_manifests/` for conflicts                                   |
| `Duplicate class`         | Run `./gradlew :app:dependencies` and look for the same class in multiple transitive deps         |
| `Could not resolve`       | Check repository declarations, VPN/proxy, verify the dependency version exists                    |
| `Unresolved reference`    | Missing import, wrong module dependency, or typo; ensure the declaring module is on the classpath |
| `Type mismatch`           | Wrong generic, nullable vs non-null, or API change after a dependency bump                        |
| `@Composable invocations` | Composable called from a non-`@Composable` context; lift the call or wrap in a composable         |
| `AAPT` / resource errors  | Invalid XML, bad `@drawable` reference, or merge conflict in `res/`                               |
| `D8/R8: Type not present` | Missing `-keep` rule or desugaring issue; check `minSdk` vs API used                              |
| `KSP error`               | Look for the processor's own error message above the Gradle wrapper                               |

### Dependency Investigation

```bash
# Full dependency tree for a configuration
./gradlew :app:dependencies --configuration releaseRuntimeClasspath

# Run with stacktrace for deeper errors
./gradlew assembleDebug --stacktrace --info
```

## Compose Recomposition Debugging

### Identifying Excessive Recomposition

1. **Layout Inspector** (Android Studio) - enable "Show recomposition counts" to find hot paths
2. Temporary `SideEffect` logging:

```kotlin
@Composable
fun MyScreen(state: UiState) {
    SideEffect { Log.d("Recompose", "MyScreen recomposed") }
    // ...
}
```

### Common Causes

- `State` objects created inside composition without `remember`
- Missing `equals()` on state data classes - a new instance with the same values still triggers
  recomposition if structural equality is not implemented
- Unstable lambda references (relevant only if Strong Skipping Mode is disabled - it is enabled
  by default since Compose Compiler 2.0+/Kotlin 2.0+, which auto-memoizes lambdas)

For stability annotations (`@Immutable`, `@Stable`) and Compose compiler metrics, see
[compose-patterns.md](compose-patterns.md#stability-annotations-immutable-vs-stable) and
[android-performance.md](android-performance.md).

## Multi-Layer Boundary Debugging

For issues spanning multiple layers (Repository, ViewModel, UI), temporarily instrument each
boundary to identify which layer produces the bad value:

```kotlin
class UserRepository @Inject constructor(
    private val api: UserApiService
) {
    suspend fun fetchUser(id: String): Result<User> {
        Log.d("DEBUG_LAYER", "Repository: fetching user $id")
        return runCatching { api.getUser(id) }
            .also { Log.d("DEBUG_LAYER", "Repository: result=$it") }
    }
}
```

Identify the layer that produces incorrect data, then investigate that layer in isolation.
Remove debug logging before committing.

## ADB Quick Reference

```bash
# List connected devices
adb devices

# Install APK
adb install -r app-debug.apk

# Launch activity
adb shell am start -n com.example.app/.MainActivity

# Clear app data
adb shell pm clear com.example.app

# Take screenshot
adb exec-out screencap -p > screen.png

# View running processes
adb shell ps | grep com.example

# Inspect app's local storage
adb shell run-as com.example.app ls /data/data/com.example.app/

# Forward device port to host (for debugging network traffic)
adb forward tcp:8080 tcp:8080

# Show memory usage
adb shell dumpsys meminfo com.example.app

# Show battery usage
adb shell dumpsys batterystats com.example.app

# Show graphics performance
adb shell dumpsys gfxinfo com.example.app

# Monitor frame rates
adb shell dumpsys gfxinfo com.example.app framestats
```

## Red Flags

- Fixing a crash without reading the full `Caused by:` chain
- Guessing at an R8 issue without checking the mapping file
- Adding `Thread.sleep()` to "fix" an ANR or race condition
- Resolving a dependency conflict with `exclude` without understanding why the duplicate exists
- Wrapping a Compose bug in `key()` without understanding what triggers recomposition
