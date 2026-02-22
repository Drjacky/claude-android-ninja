/*
 * Convention plugin for Android application modules
 * Configures: Android, Lint, Dependency Guard
 * Note: AGP 9+ has built-in Kotlin support, no need for kotlin-android plugin
 */

import com.android.build.api.dsl.ApplicationExtension
import com.android.build.api.variant.ApplicationAndroidComponentsExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure

class AndroidApplicationConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "com.android.application")
            apply(plugin = "app.android.lint")

            extensions.configure<ApplicationExtension> {
                configureKotlinAndroid(this)
                
                defaultConfig {
                    targetSdk = libs.findVersion("targetSdk").get().toString().toInt()
                    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
                }
                
                testOptions {
                    animationsDisabled = true
                }
                
                configureGradleManagedDevices(this)
            }
            
            extensions.configure<ApplicationAndroidComponentsExtension> {
                configurePrintApksTask(this)
            }
        }
    }
}
