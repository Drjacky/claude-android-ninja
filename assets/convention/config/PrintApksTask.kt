/*
 * Print APKs task configuration
 * Creates task to print all generated APK paths
 */

import com.android.build.api.variant.AndroidComponentsExtension
import org.gradle.api.Project
import org.gradle.kotlin.dsl.register

/**
 * Configure task to print all APK paths for a project
 * Usage: ./gradlew printApks
 */
internal fun Project.configurePrintApksTask(
    extension: AndroidComponentsExtension<*, *, *>,
) {
    extension.onVariants { variant ->
        tasks.register("print${variant.name.capitalize()}Apks") {
            group = "help"
            description = "Prints all APK paths for ${variant.name} variant"
            
            doLast {
                println("APKs for ${variant.name}:")
                variant.artifacts.getAll(com.android.build.api.artifact.SingleArtifact.APK)
                    .forEach { apk ->
                        println("  - ${apk.absolutePath}")
                    }
            }
        }
    }
}
