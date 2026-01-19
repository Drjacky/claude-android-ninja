# Dependencies Guide

Use this guide for dependency selection and version catalog updates in all Android projects and features.

## When to Use This Guide
- **New project**: Start by reviewing the version catalog template.
- **New feature**: Confirm required libraries are already defined.
- **Any new code**: Verify you are using approved dependencies and versions.

## Version Catalog Source of Truth
Always check `templates/libs.versions.toml.template` before adding or changing dependencies.

### Rules
1. **Prefer existing entries** in the template when adding dependencies.
2. **If a dependency is missing**, add it to `libs.versions.toml` following the same grouping and naming conventions.
3. **Keep versions centralized** in the `libs.versions.toml`; reference them by `version.ref`.
4. **Use bundles** when multiple libraries are typically used together (e.g., Compose, Navigation).

## Adding a New Dependency
1. Review `templates/libs.versions.toml.template`.
2. Add the dependency under the appropriate section in the `libs.versions.toml`:
   - `versions` for new version keys
   - `libraries` for individual artifacts
   - `bundles` for grouped dependencies
   - `plugins` for Gradle plugins
3. Use the new added entry in your module `build.gradle.kts`.

## Example
```toml
# libs.versions.toml
[versions]
retrofit = "2.11.0"

[libraries]
square-retrofit = { group = "com.squareup.retrofit2", name = "retrofit", version.ref = "retrofit" }
```

```kotlin
// build.gradle.kts
dependencies {
    implementation(libs.square.retrofit)
}
```
