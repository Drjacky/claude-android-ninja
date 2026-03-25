/*
 * Optional Gradle task: entry point for Play Developer Reporting API + Slack.
 * Add PlayVitalsRepository, Reporting API deps, and timeline helpers per references/android-performance.md
 */

import kotlinx.coroutines.runBlocking
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
        runBlocking {
            logger.lifecycle(
                "Play vitals: env OK for $app. Add PlayVitalsRepository and uncomment the lines below (see references/android-performance.md).",
            )
            // Add PlayVitalsRepository to this module and catalog deps, then uncomment:
            // val repository = PlayVitalsRepository(appName = app, serviceAccountJson = json)
            // val timeline = buildTimelineSpecDaily(...) // GooglePlayDeveloperReportingV1beta1TimelineSpec
            // val request = GooglePlayDeveloperReportingV1beta1QueryAnrRateMetricSetRequest()
            //     .setTimelineSpec(timeline)
            //     .setMetrics(listOf("anrRate", "anrRate7dUserWeighted", "anrRate28dUserWeighted", ...))
            // val summary = repository.queryAnrRates(request)
            // postToSlackAnr(summary) // if summary is null, post "ANR: n/a" or omit section; task still succeeds
        }
    }
}
