/*
 * Convention plugin for Room database modules
 * Configures: Room 3 plugin, KSP, schema directory, bundled SQLite driver
 */

import androidx.room3.gradle.RoomExtension
import com.google.devtools.ksp.gradle.KspExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.apply
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies

class AndroidRoomConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            apply(plugin = "androidx.room3")
            apply(plugin = "com.google.devtools.ksp")

            extensions.configure<KspExtension> {
                arg("room.generateKotlin", "true")
            }

            extensions.configure<RoomExtension>("room3") {
                // Schema directory for Room auto migrations
                // See https://developer.android.com/reference/kotlin/androidx/room3/AutoMigration
                schemaDirectory("$projectDir/schemas")
            }

            dependencies {
                add("implementation", libs.findLibrary("room3.runtime").get())
                add("implementation", libs.findLibrary("androidx.sqlite.bundled").get())
                add("ksp", libs.findLibrary("room3.compiler").get())
            }
        }
    }
}
