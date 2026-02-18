/*
 * Convention plugin for baseline profile generation
 * Configures: Baseline profile plugin for performance optimization
 * Applies to: App module
 */

import com.android.build.api.dsl.ApplicationExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

class AndroidApplicationBaselineProfileConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "androidx.baselineprofile")

            extensions.configure<ApplicationExtension> {
                // Baseline profile configuration is handled by the plugin
                // Just ensure we have the dependency
            }

            dependencies {
                // Reference to baselineprofile module (if exists)
                // add("baselineProfile", project(":baselineprofile"))
            }
        }
    }
}
