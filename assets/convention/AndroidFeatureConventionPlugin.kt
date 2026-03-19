/*
 * Convention plugin for feature implementation modules
 * Configures: Feature module with UI, ViewModel, Hilt, Navigation3
 * Applies to: feature/:feature-name modules
 */

import com.android.build.api.dsl.LibraryExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

class AndroidFeatureConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "app.android.library")
            apply(plugin = "app.android.library.compose")
            apply(plugin = "app.hilt")

            extensions.configure<LibraryExtension> {
                testOptions {
                    animationsDisabled = true
                }
                configureGradleManagedDevices(this)
            }

            dependencies {
                // Core dependencies
                add("implementation", project(":core:ui"))
                add("implementation", project(":core:domain"))
                add("implementation", project(":core:data"))

                // Lifecycle
                add("implementation", libs.findLibrary("androidx.lifecycle.runtime.compose").get())
                add("implementation", libs.findLibrary("androidx.lifecycle.viewmodel.compose").get())
                
                // Navigation3
                add("implementation", libs.findLibrary("androidx.navigation3.runtime").get())
                add("implementation", libs.findLibrary("androidx.navigation3.compose").get())

                // Adaptive layouts (NavigationSuiteScaffold, ListDetailPaneScaffold, SupportingPaneScaffold)
                libs.findBundle("adaptive").ifPresent { add("implementation", it) }

                // Testing
                add("androidTestImplementation", libs.findLibrary("androidx.lifecycle.runtime.compose").get())
            }
        }
    }
}
