/*
 * Optional Gradle task: placeholder for Play Developer Reporting API + Slack.
 * Add PlayVitalsRepository and API calls per references/android-performance.md
 */

import org.gradle.api.DefaultTask
import org.gradle.api.tasks.TaskAction

abstract class PlayVitalsReportingTask : DefaultTask() {

    @TaskAction
    fun report() {
        val json = System.getenv("PLAY_REPORTING_SERVICE_ACCOUNT_JSON")
        val app = System.getenv("PLAY_REPORTING_APP_RESOURCE")
        if (json.isNullOrBlank() || app.isNullOrBlank()) {
            logger.warn(
                "Skipping play vitals report: set PLAY_REPORTING_SERVICE_ACCOUNT_JSON " +
                    "and PLAY_REPORTING_APP_RESOURCE",
            )
            return
        }
        logger.lifecycle(
            "Play vitals: env present for $app. Wire PlayVitalsRepository per references/android-performance.md",
        )
    }
}
