/*
 * Convention plugin for Android library modules
 * Configures: Android, Lint, Testing
 * Note: AGP 9+ has built-in Kotlin support, no need for kotlin-android plugin
 */

import com.android.build.api.dsl.LibraryExtension
import com.android.build.api.variant.LibraryAndroidComponentsExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

class AndroidLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "com.android.library")
            apply(plugin = "app.android.lint")

            extensions.configure<LibraryExtension> {
                configureKotlinAndroid(this)
                
                defaultConfig {
                    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
                    
                    // Version catalog entries for targetSdk
                    testOptions.targetSdk = libs.findVersion("targetSdk").get().toString().toInt()
                    lint.targetSdk = libs.findVersion("targetSdk").get().toString().toInt()
                }
                
                testOptions {
                    animationsDisabled = true
                }
                
                configureGradleManagedDevices(this)
                
                // Resource prefix based on module path
                // :core:data → core_data_
                resourcePrefix = path.split("""\W""".toRegex())
                    .drop(1)
                    .distinct()
                    .joinToString(separator = "_")
                    .lowercase() + "_"
            }
            
            extensions.configure<LibraryAndroidComponentsExtension> {
                configurePrintApksTask(this)
                disableUnnecessaryAndroidTests(target)
            }
            
            dependencies {
                add("androidTestImplementation", libs.findLibrary("kotlin.test").get())
                add("testImplementation", libs.findLibrary("kotlin.test").get())
                add("testImplementation", libs.findLibrary("junit").get())
            }
        }
    }
}
