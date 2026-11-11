import java.util.Properties

plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

val keystoreFile = rootProject.file("key.properties")
val keystore = Properties().apply {
    if (keystoreFile.exists()) keystoreFile.inputStream().use { load(it) }
}
// Debug builds do not need release credentials. Release builds never use debug keys.
val isReleaseBuild = gradle.startParameter.taskNames.any { it.contains("release", ignoreCase = true) }
if (isReleaseBuild && listOf("storeFile", "storePassword", "keyAlias", "keyPassword").any {
    keystore.getProperty(it).isNullOrBlank()
}) {
    throw GradleException("Release signing is not configured. See docs/CLOUD_BETA_RELEASE_VI.md.")
}

android {
    namespace = "com.example.documind_mobile"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        applicationId = "com.ncdanh0311.documind"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        create("release") {
            keyAlias = keystore.getProperty("keyAlias")
            keyPassword = keystore.getProperty("keyPassword")
            storeFile = keystore.getProperty("storeFile")?.let { file(it) }
            storePassword = keystore.getProperty("storePassword")
        }
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
        release {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}

flutter {
    source = "../.."
}
