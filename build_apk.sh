#!/bin/bash
# ============================================================
# AfrikaBurn 2026 — Android APK Build Script
# Uses the high-res portrait SVG for maximum quality
# ============================================================

set -e  # exit on error

REPO=~/git_projects/afrikaburnmap-2026
WWW=$REPO/www
INDEX=$WWW/index.html

WEB_IMAGE="2026_map_landscape.svg"
APK_IMAGE="2026_map_portrait.png"

echo "==> Switching to portrait SVG for APK build..."
sed -i "s/src=\"$WEB_IMAGE\"/src=\"$APK_IMAGE\"/" $INDEX

echo "==> Copying web assets to Android..."
cd $REPO
npx cap copy android

echo "==> Building release APK..."
cd $REPO/android
./gradlew assembleRelease --rerun-tasks

echo "==> Switching back to landscape SVG for web..."
sed -i "s/src=\"$APK_IMAGE\"/src=\"$WEB_IMAGE\"/" $INDEX

APK=$REPO/android/app/build/outputs/apk/release/app-release.apk
NAMED_APK=$REPO/android/app/build/outputs/apk/release/AfrikaBurn2026.apk
mv $APK $NAMED_APK

echo ""
echo "✓ Done! APK at: $NAMED_APK"
ls -lh $NAMED_APK
