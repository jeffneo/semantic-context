#!/bin/sh
# Builds target/qlsc-vg-passthrough.jar with the JDK alone (javac, jar): no dependencies to download.
# Runs the self-test first; the jar is mounted in the neo4j-vg container in place of the real driver.
set -e
cd "$(dirname "$0")"
rm -rf target/classes target/test && mkdir -p target/classes target/test  # the jar itself is replaced in place: the container mounts it
javac --release 21 -d target/classes $(find src -name '*.java')
javac --release 21 -cp target/classes -d target/test $(find test -name '*.java')
java -cp target/classes:target/test qlsc.passthrough.SelfTest
mkdir -p target/classes/META-INF/services
echo com.google.cloud.bigquery.jdbc.BigQueryDriver > target/classes/META-INF/services/java.sql.Driver
jar --create --file target/qlsc-vg-passthrough.jar.new -C target/classes . && cat target/qlsc-vg-passthrough.jar.new > target/qlsc-vg-passthrough.jar && rm target/qlsc-vg-passthrough.jar.new
echo "-> $(pwd)/target/qlsc-vg-passthrough.jar"
