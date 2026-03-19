/*
 * Convention plugin for Android test modules
 * Configures: Test modules for instrumentation testing
 * Applies to: test modules (e.g., :benchmark, :baselineprofile)
 * Note: AGP 9+ has built-in Kotlin support, no need for kotlin-android plugin
 */

import com.android.build.api.dsl.TestExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure

class AndroidTestConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "com.android.test")

            extensions.configure<TestExtension> {
                configureKotlinAndroid(this)
                
                defaultConfig {
                    targetSdk = libs.findVersion("targetSdk").get().toString().toInt()
                }
                
                configureGradleManagedDevices(this)
            }
        }
    }
}
