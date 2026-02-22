/*
 * Convention plugin for Detekt static analysis
 * Configures: Detekt plugin, Compose rules, baseline, type resolution
 */

import io.gitlab.arturbosch.detekt.Detekt
import io.gitlab.arturbosch.detekt.DetektCreateBaselineTask
import io.gitlab.arturbosch.detekt.extensions.DetektExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.JavaPluginExtension
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType
import org.gradle.kotlin.dsl.withType

class DetektConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        val detektPluginId = libs.findPlugin("detekt").get().get().pluginId

        pluginManager.apply(detektPluginId)

        dependencies {
            // Compose ruleset for Jetpack Compose best practices
            add("detektPlugins", libs.findLibrary("compose.rules.detekt").get())
        }

        extensions.configure<DetektExtension> {
            buildUponDefaultConfig = true
            basePath = rootProject.projectDir.absolutePath
            parallel = true
            
            // Use central config file
            config.from(rootProject.file("config/detekt.yml"))
            
            // Allow local overrides
            val moduleConfig = project.file("detekt.yml")
            if (moduleConfig.exists()) {
                config.from(moduleConfig)
            }
            
            // Baseline file (optional, per module)
            baseline = project.file("detekt-baseline.xml")
        }

        // Configure Detekt tasks
        tasks.withType<Detekt>().configureEach {
            jvmTarget = "17"
            
            // XML and HTML reports
            reports {
                xml.required.set(true)
                html.required.set(true)
                txt.required.set(false)
                sarif.required.set(true)
                md.required.set(false)
            }
            
            // JVM modules get classpath from JavaPluginExtension for type resolution
            if (project.pluginManager.hasPlugin("org.jetbrains.kotlin.jvm")) {
                val javaExtension = extensions.findByType(JavaPluginExtension::class.java)
                javaExtension?.let {
                    classpath.from(it.sourceSets.getByName("main").compileClasspath)
                }
            }
        }

        // Configure baseline task
        tasks.withType<DetektCreateBaselineTask>().configureEach {
            jvmTarget = "17"
        }
    }
}
