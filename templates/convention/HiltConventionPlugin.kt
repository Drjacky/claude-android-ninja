/*
 * Convention plugin for Hilt dependency injection
 * Configures: Hilt plugin, KSP compiler, common dependencies
 */

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.dependencies

class HiltConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "com.google.devtools.ksp")
            apply(plugin = "dagger.hilt.android.plugin")

            dependencies {
                add("implementation", libs.findLibrary("hilt.android").get())
                add("ksp", libs.findLibrary("hilt.compiler").get())
                
                // For testing
                add("kspTest", libs.findLibrary("hilt.compiler").get())
                add("testImplementation", libs.findLibrary("hilt.android.testing").get())
                add("kspAndroidTest", libs.findLibrary("hilt.compiler").get())
                add("androidTestImplementation", libs.findLibrary("hilt.android.testing").get())
            }
        }
    }
}
