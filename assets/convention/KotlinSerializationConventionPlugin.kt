/*
 * Convention plugin for Kotlin Serialization
 * Configures: kotlinx-serialization for JSON/data serialization
 * Applies to: Modules that need JSON serialization (e.g., network, data)
 */

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.dependencies

class KotlinSerializationConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "org.jetbrains.kotlin.plugin.serialization")

            dependencies {
                add("implementation", libs.findLibrary("kotlinx.serialization").get())
            }
        }
    }
}
