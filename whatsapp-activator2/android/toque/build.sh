#!/bin/sh
# Compila o Toque.apk dentro de um contêiner descartável com Java (não precisa de nada instalado
# na máquina). Uso, na pasta com estes arquivos:
#   docker run --rm -v "$PWD":/w -w /w eclipse-temurin:17-jdk sh build.sh
# O SDK baixado fica em .sdk/ (reaproveitado na próxima vez); a chave de assinatura em chave.jks
# (a mesma chave é necessária para reinstalar por cima).
set -e
apt-get update -qq >/dev/null && apt-get install -y -qq curl unzip zip >/dev/null
SDK=/w/.sdk
BT=$SDK/build-tools/34.0.0
JAR=$SDK/platforms/android-31/android.jar
if [ ! -x "$BT/aapt2" ] || [ ! -f "$JAR" ]; then
  mkdir -p $SDK/cmdline-tools
  curl -fsSL -o /tmp/ct.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
  rm -rf $SDK/cmdline-tools/latest && unzip -q /tmp/ct.zip -d /tmp/ct && mv /tmp/ct/cmdline-tools $SDK/cmdline-tools/latest
  yes | $SDK/cmdline-tools/latest/bin/sdkmanager --sdk_root=$SDK "build-tools;34.0.0" "platforms;android-31" >/dev/null
fi
rm -rf /tmp/b && mkdir -p /tmp/b/cls /tmp/b/dex
$BT/aapt2 compile --dir res -o /tmp/b/res.zip
$BT/aapt2 link -o /tmp/b/base.apk -I $JAR --manifest AndroidManifest.xml /tmp/b/res.zip \
  --min-sdk-version 26 --target-sdk-version 30 --version-code 1 --version-name 1
javac -source 8 -target 8 -bootclasspath $JAR -nowarn -d /tmp/b/cls src/com/waa11y/*.java
$BT/d8 --min-api 26 --lib $JAR --output /tmp/b/dex $(find /tmp/b/cls -name '*.class')
(cd /tmp/b/dex && zip -q /tmp/b/base.apk classes.dex)
$BT/zipalign -f 4 /tmp/b/base.apk /tmp/b/aligned.apk
[ -f chave.jks ] || keytool -genkeypair -keystore chave.jks -storepass android -keypass android \
  -alias toque -keyalg RSA -keysize 2048 -validity 10000 -dname CN=toque >/dev/null 2>&1
$BT/apksigner sign --ks chave.jks --ks-pass pass:android --out Toque.apk /tmp/b/aligned.apk
echo "pronto: Toque.apk"
