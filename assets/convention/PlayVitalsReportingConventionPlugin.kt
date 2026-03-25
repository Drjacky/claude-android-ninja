/*
 * Optional: registers playVitalsReport on the root project only.
 * See references/android-performance.md and references/gradle-setup.md
 */

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.register

class PlayVitalsReportingConventionPlugin : Plugin<Project> {
    override fun apply(project: Project) {
        check(project == project.rootProject) {
            "app.play.vitals must be applied only in the root build.gradle.kts"
        }
        project.tasks.register<PlayVitalsReportingTask>("playVitalsReport") {
            group = "reporting"
            description =
                "Optional: Play Developer Reporting API vitals (see references/android-performance.md)"
        }
    }
}
