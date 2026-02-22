/*
 * Kotlin and Android configuration utilities
 * Configures: compileSdk, minSdk, Java version, Kotlin compiler options
 */

import com.android.build.api.dsl.CommonExtension
import org.gradle.api.JavaVersion
import org.gradle.api.Project
import org.gradle.api.plugins.JavaPluginExtension
import org.gradle.kotlin.dsl.assign
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.dsl.KotlinAndroidProjectExtension
import org.jetbrains.kotlin.gradle.dsl.KotlinBaseExtension
import org.jetbrains.kotlin.gradle.dsl.KotlinJvmProjectExtension

/**
 * Configure base Kotlin with Android options
 */
internal fun Project.configureKotlinAndroid(
    commonExtension: CommonExtension<*, *, *, *, *, *>,
) {
    commonExtension.apply {
        compileSdk {
            version = release(libs.findVersion("compileSdk").get().toString().toInt())
        }

        defaultConfig.apply {
            minSdk = libs.findVersion("minSdk").get().toString().toInt()
        }

        compileOptions.apply {
            sourceCompatibility = JavaVersion.VERSION_17
            targetCompatibility = JavaVersion.VERSION_17
            isCoreLibraryDesugaringEnabled = true // Required for API < 26 (java.time, Duration API)
        }
    }

    configureKotlin<KotlinAndroidProjectExtension>()

    dependencies {
        add("coreLibraryDesugaring", libs.findLibrary("androidx.core.desugaring").get())
    }
}

/**
 * Configure base Kotlin options for JVM (non-Android)
 */
internal fun Project.configureKotlinJvm() {
    extensions.configure<JavaPluginExtension> {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    configureKotlin<KotlinJvmProjectExtension>()
}

/**
 * Configure base Kotlin options
 */
private inline fun <reified T : KotlinBaseExtension> Project.configureKotlin() =
    configure<T> {
        // Treat all Kotlin warnings as errors (disabled by default)
        // Override by setting warningsAsErrors=true in your ~/.gradle/gradle.properties
        val warningsAsErrors = providers.gradleProperty("warningsAsErrors")
            .map { it.toBoolean() }
            .orElse(false)

        when (this) {
            is KotlinAndroidProjectExtension -> compilerOptions
            is KotlinJvmProjectExtension -> compilerOptions
            else -> TODO("Unsupported project extension $this ${T::class}")
        }.apply {
            jvmTarget = JvmTarget.JVM_17
            allWarningsAsErrors = warningsAsErrors
            
            freeCompilerArgs.addAll(
                // Enable experimental coroutines APIs, including Flow
                "-opt-in=kotlinx.coroutines.ExperimentalCoroutinesApi",
                // Enable experimental Material3 APIs
                "-opt-in=androidx.compose.material3.ExperimentalMaterial3Api",
                // Enable experimental Material3 Adaptive APIs
                "-opt-in=androidx.compose.material3.adaptive.ExperimentalMaterial3AdaptiveApi",
                // Enable experimental Foundation APIs
                "-opt-in=androidx.compose.foundation.ExperimentalFoundationApi",
            )
        }
    }
