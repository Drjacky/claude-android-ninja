/*
 * Convention plugin for pure JVM/Kotlin library modules
 * Configures: Kotlin JVM libraries without Android dependencies
 * Applies to: Pure Kotlin modules (e.g., :core:model, utility modules)
 */

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.dependencies

class JvmLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "org.jetbrains.kotlin.jvm")
            apply(plugin = "app.android.lint")

            configureKotlinJvm()
            
            dependencies {
                add("testImplementation", libs.findLibrary("kotlin.test").get())
            }
        }
    }
}
