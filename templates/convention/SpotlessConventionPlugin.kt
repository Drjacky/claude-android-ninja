/*
 * Convention plugin for Spotless code formatting
 * Configures: ktlint, license headers, formatting
 * Applies to: All modules for consistent code style
 */

import com.diffplug.gradle.spotless.SpotlessExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure

class SpotlessConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "com.diffplug.spotless")

            extensions.configure<SpotlessExtension> {
                kotlin {
                    target("src/**/*.kt")
                    ktlint(libs.findVersion("ktlint").get().requiredVersion)
                        .editorConfigOverride(
                            mapOf(
                                "android" to "true",
                                "max_line_length" to "120"
                            )
                        )
                    trimTrailingWhitespace()
                    endWithNewline()
                }

                format("kts") {
                    target("*.kts", "**/*.kts")
                    trimTrailingWhitespace()
                    endWithNewline()
                }

                // Format XML files (layouts, resources)
                if (pluginManager.hasPlugin("com.android.library") ||
                    pluginManager.hasPlugin("com.android.application")
                ) {
                    format("xml") {
                        target("src/**/*.xml")
                        trimTrailingWhitespace()
                        indentWithSpaces(4)
                        endWithNewline()
                    }
                }
            }
        }
    }
}
