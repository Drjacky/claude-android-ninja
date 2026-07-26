/*
 * Convention plugin for Firebase integration
 * Configures: Firebase Crashlytics, Analytics
 * Applies to: App module when using Firebase
 */

import com.google.firebase.crashlytics.buildtools.gradle.CrashlyticsExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

class FirebaseConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "com.google.gms.google-services")
            apply(plugin = "com.google.firebase.crashlytics")

            dependencies {
                val bom = libs.findLibrary("firebase.bom").get()
                add("implementation", platform(bom))
                add("implementation", libs.findLibrary("firebase.analytics").get())
                add("implementation", libs.findLibrary("firebase.crashlytics").get())
            }

            extensions.configure<CrashlyticsExtension> {
                // Only enable for projects that actually ship native libraries. When true, the
                // plugin requires a symbol generator and unstripped .so inputs, so enabling it
                // on a pure-Kotlin app fails the release build.
                nativeSymbolUploadEnabled = providers
                    .gradleProperty("app.crashlytics.nativeSymbols")
                    .map { it.toBoolean() }
                    .getOrElse(false)

                // Skip mapping upload for debug builds; release builds must upload it or
                // production stack traces cannot be de-obfuscated.
                if (project.gradle.startParameter.taskNames.any { it.contains("Debug") }) {
                    mappingFileUploadEnabled = false
                }
            }
        }
    }
}
