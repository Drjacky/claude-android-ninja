/*
 * Convention plugin for Detekt static analysis
 * Configures: Detekt plugin, Compose rules, baseline, type resolution
 * Note: Detekt 2.0+ uses dev.detekt package and new report names
 */

import dev.detekt.gradle.Detekt
import dev.detekt.gradle.DetektCreateBaselineTask
import dev.detekt.gradle.extensions.DetektExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.JavaPluginExtension
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.withType

class DetektConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        val detektPluginId = libs.findPlugin("detekt").get().get().pluginId

        pluginManager.apply(detektPluginId)

        dependencies {
            add("detektPlugins", libs.findLibrary("compose.rules.detekt").get())
        }

        extensions.configure<DetektExtension> {
            buildUponDefaultConfig = true
            basePath = rootProject.projectDir.absolutePath
            parallel = true
            
            config.from(rootProject.file("config/detekt.yml"))
            
            val moduleConfig = project.file("detekt.yml")
            if (moduleConfig.exists()) {
                config.from(moduleConfig)
            }
            
            baseline = project.file("detekt-baseline.xml")
        }

        tasks.withType<Detekt>().configureEach {
            jvmTarget = "17"
            
            reports {
                checkstyle.required.set(true)
                html.required.set(true)
                txt.required.set(false)
                sarif.required.set(true)
                markdown.required.set(false)
            }
            
            if (project.pluginManager.hasPlugin("org.jetbrains.kotlin.jvm")) {
                val javaExtension = extensions.findByType(JavaPluginExtension::class.java)
                javaExtension?.let {
                    classpath.from(it.sourceSets.getByName("main").compileClasspath)
                }
            }
        }

        tasks.withType<DetektCreateBaselineTask>().configureEach {
            jvmTarget = "17"
        }
    }
}
