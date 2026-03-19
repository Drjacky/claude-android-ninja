/*
 * Convention plugin for Sentry integration
 * Configures: Sentry SDK, Compose integration, Kotlin compiler plugin
 * Applies to: App module when using Sentry for crash reporting
 */

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.dependencies

class SentryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "io.sentry.android.gradle")
            apply(plugin = "io.sentry.kotlin.compiler.gradle")

            dependencies {
                add("implementation", libs.findLibrary("sentry.android").get())
                add("implementation", libs.findLibrary("sentry.compose.android").get())
            }
        }
    }
}
