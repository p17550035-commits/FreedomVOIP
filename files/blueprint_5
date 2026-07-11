# FreedomVOIP Auto-Update Workflow Blueprint  
Automatic Version Bumps + Automatic Builds + Automatic Tagging + Automatic Releases + Dependency Update Triggers

====================================================================
1. WORKFLOW PURPOSE
====================================================================

This workflow keeps FreedomVOIP updated automatically by:

- bumping versionCode and versionName
- rebuilding APKs on every update
- tagging releases automatically
- publishing releases automatically
- rebuilding when dependencies update
- sending email notifications on success/failure
- keeping the repo fully reproducible

This eliminates all manual build steps.

====================================================================
2. VERSIONING STRATEGY
====================================================================

Version files:
- gradle.properties
- app/build.gradle

Auto-bump rules:
- versionCode increments on every build
- versionName increments on tagged builds
- patch version increments on dependency updates

Example:
versionCode=104
versionName=1.0.4

====================================================================
3. TRIGGER RULES
====================================================================

Workflow triggers on:

1. Push to main
2. Merge into main
3. New tag (vX.Y.Z)
4. Dependency updates (Renovate / Dependabot)
5. Manual dispatch (button click)
6. Scheduled nightly build (optional)

====================================================================
4. WORKFLOW STEPS
====================================================================

Step 1 — Checkout repo  
Step 2 — Read current version  
Step 3 — Auto-increment versionCode  
Step 4 — Auto-update versionName if tagged  
Step 5 — Commit version bump  
Step 6 — Tag release (vX.Y.Z)  
Step 7 — Install JDK  
Step 8 — Install Android SDK  
Step 9 — Install build-tools + platform-tools  
Step 10 — Run Gradle wrapper  
Step 11 — Build APK (debug + release)  
Step 12 — Sign APK (if signing keys provided)  
Step 13 — Upload APK as artifact  
Step 14 — Publish GitHub Release  
Step 15 — Email notification on success/failure

====================================================================
5. DEPENDENCY UPDATE TRIGGER
====================================================================

Dependabot or Renovate can update:

- Gradle dependencies
- WebRTC libraries
- Kotlin version
- AndroidX libraries
- Security patches

When a dependency PR merges:
- workflow auto-bumps version
- workflow auto-builds APK
- workflow auto-tags release
- workflow auto-publishes release

====================================================================
6. EMAIL NOTIFICATIONS
====================================================================

GitHub automatically emails:
- build failures
- build successes (optional)
- new releases
- new tags
- dependency alerts
- runner errors

No configuration needed.

====================================================================
7. WORKFLOW YAML (STRUCTURE OUTLINE)
====================================================================

name: FreedomVOIP Auto-Build

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]
  workflow_dispatch:
  schedule:
    - cron: "0 3 * * *"
  create:
    tags:
      - "v*"
  repository_dispatch:
    types: [ "dependency-update" ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - Checkout repo
      - Read version
      - Bump versionCode
      - Update versionName if tag exists
      - Commit version bump
      - Tag release
      - Install JDK
      - Install Android SDK
      - Install build-tools
      - Install platform-tools
      - Run Gradle wrapper
      - Build APK
      - Sign APK
      - Upload artifact
      - Publish release

====================================================================
8. ARTIFACT NAMING
====================================================================

Artifacts:
- FreedomVOIP-vX.Y.Z-release.apk
- FreedomVOIP-vX.Y.Z-debug.apk
- FreedomVOIP-agent-vX.Y.Z.apk
- FreedomVOIP-server-bundle-vX.Y.Z.zip

====================================================================
9. RELEASE NAMING
====================================================================

Release tags:
v1.0.4  
v1.0.5  
v1.1.0  

Release titles:
FreedomVOIP v1.0.4 — Auto Build  
FreedomVOIP v1.1.0 — Dependency Update  

====================================================================
10. CHANGELOG AUTOMATION
====================================================================

Auto-generated changelog includes:
- commit messages
- dependency updates
- version bump
- build status
- APK download links

====================================================================
11. SIGNING KEY HANDLING
====================================================================

Signing keys stored in:
GitHub Secrets → ANDROID_KEYSTORE_BASE64  
GitHub Secrets → ANDROID_KEYSTORE_PASSWORD  
GitHub Secrets → ANDROID_KEY_ALIAS  
GitHub Secrets → ANDROID_KEY_PASSWORD  

Runner decodes and signs automatically.

====================================================================
12. F-DROID COMPATIBILITY
====================================================================

F-Droid metadata auto-updated:
- versionCode
- versionName
- changelog
- source tarball URL
- APK URL

====================================================================
END OF FREEDOMVOIP AUTO-UPDATE WORKFLOW BLUEPRINT
====================================================================
