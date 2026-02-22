/*
 * Android instrumentation test utilities
 * Configures: Disable unnecessary Android tests for non-UI modules
 */

import com.android.build.api.variant.LibraryAndroidComponentsExtension
import org.gradle.api.Project

/**
 * Disable unnecessary Android instrumentation tests for modules without UI
 * This improves build performance by skipping test APK generation
 */
internal fun LibraryAndroidComponentsExtension.disableUnnecessaryAndroidTests(
    project: Project,
) = beforeVariants {
    it.enableAndroidTest = it.enableAndroidTest &&
            project.projectDir.resolve("src/androidTest").exists()
}
