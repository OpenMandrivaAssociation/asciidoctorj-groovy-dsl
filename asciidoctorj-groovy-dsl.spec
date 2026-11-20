Name:		asciidoctorj-groovy-dsl
Version:	3.0.0.beta.2
Release:	2
Summary:	Groovy DSL for AsciidoctorJ extensions
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/asciidoctor/asciidoctorj-groovy-dsl
# Tag v3.0.0-beta.2. The Gradle tool is not invoked. Sources are
# compiled with Groovy's FileSystemCompiler at bytecode 17 because
# asciidoctorj's ExtensionRegistry class file is major version 71.
Source0:	asciidoctorj-groovy-dsl-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	apache-groovy
BuildRequires:	antlr4
BuildRequires:	objectweb-asm
BuildRequires:	picocli
BuildRequires:	jansi
BuildRequires:	ant-lib
BuildRequires:	asciidoctorj
BuildRequires:	mvn(org.asciidoctor:asciidoctorj) = 3.0.1
BuildRequires:	mvn(org.asciidoctor:asciidoctorj-api) = 3.0.1
BuildRequires:	mvn(org.jruby:jruby) = 10.1.3.0
BuildRequires:	mvn(ch.randelshofer:fastdoubleparser)
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
Requires:	apache-groovy
Requires:	asciidoctorj
%{!?jruby_jar:%global jruby_jar %{_javadir}/jruby.jar}
%{!?dirgra_jar:%global dirgra_jar %{_javadir}/dirgra.jar}
%{!?invokebinder_jar:%global invokebinder_jar %{_javadir}/invokebinder.jar}
%{!?asciidoctorj_jar:%global asciidoctorj_jar %{_javadir}/asciidoctorj.jar}

%description
org.asciidoctor:asciidoctorj-groovy-dsl %{version}. AsciidoctorExtensions
registers a Groovy postprocessor with AsciidoctorJ, and convert then
runs that postprocessor. The Gradle tool is not invoked.

%prep
%autosetup -n asciidoctorj-groovy-dsl-%{version} -p1
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
find . -type d -name '*.jar' -print >> binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
find src/main -type f \( -name '*.groovy' -o -name '*.java' \) | sort > sources.list
test "$(wc -l < sources.list)" -eq 12
test "$(grep -c '\.groovy$' sources.list)" -eq 11
test "$(grep -c '\.java$' sources.list)" -eq 1
test -s src/main/resources/META-INF/services/org.asciidoctor.jruby.extension.spi.ExtensionRegistry

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
tool_cp=%{_javadir}/apache-groovy.jar
for extra in \
	%{_javadir}/apache-groovy-xml.jar \
	%{_javadir}/apache-groovy-json.jar \
	%{_javadir}/apache-groovy-templates.jar \
	%{_javadir}/antlr4-runtime.jar \
	%{_javadir}/asm.jar \
	%{_javadir}/asm-commons.jar \
	%{_javadir}/asm-tree.jar \
	%{_javadir}/asm-util.jar \
	%{_javadir}/asm-analysis.jar \
	%{_javadir}/picocli.jar \
	/usr/lib/java/jansi/jansi.jar \
	%{_javadir}/ant.jar
do
	test -s "$extra"
	tool_cp=$tool_cp:$extra
done
src_cp=%{asciidoctorj_jar}:%{_javadir}/asciidoctorj-api.jar:%{jruby_jar}:%{_javadir}/apache-groovy.jar
mkdir -p classes
java -Dgroovy.target.bytecode=17 -cp "$tool_cp" org.codehaus.groovy.tools.FileSystemCompiler \
	--classpath "$src_cp" -j '-J-release=17' -d classes @sources.list
test "$(find classes -name '*.class' | wc -l)" -eq 14
javap -v -classpath classes org.asciidoctor.groovydsl.AsciidoctorExtensions | grep -F -q 'major version: 61'
/bin/cp -a src/main/resources/META-INF classes/
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: org.asciidoctor.groovydsl' > manifest.mf
jar cfm asciidoctorj-groovy-dsl.jar manifest.mf -C classes .
jar i asciidoctorj-groovy-dsl.jar
jar tf asciidoctorj-groovy-dsl.jar | grep -F -q 'org/asciidoctor/groovydsl/AsciidoctorExtensions.class'
jar tf asciidoctorj-groovy-dsl.jar | grep -F -q 'META-INF/services/org.asciidoctor.jruby.extension.spi.ExtensionRegistry'
jar --describe-module --file asciidoctorj-groovy-dsl.jar > describe.txt
if grep -F -q 'Unable' describe.txt; then
	cat describe.txt
	exit 1
fi
grep -F -qx 'org.asciidoctor.groovydsl automatic' describe.txt

cat > asciidoctorj-groovy-dsl.pom << 'END'
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.asciidoctor</groupId>
  <artifactId>asciidoctorj-groovy-dsl</artifactId>
  <version>%{version}</version>
  <name>asciidoctorj-groovy-dsl</name>
  <licenses>
    <license>
      <name>Apache-2.0</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.asciidoctor</groupId>
      <artifactId>asciidoctorj</artifactId>
      <version>3.0.1</version>
    </dependency>
  </dependencies>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact asciidoctorj-groovy-dsl.pom:asciidoctorj-groovy-dsl.jar \
	--file-name asciidoctorj-groovy-dsl \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/org.asciidoctor/asciidoctorj-groovy-dsl.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "asciidoctorj-groovy-dsl"' "$idx"
test -s %{buildroot}%{_javadir}/asciidoctorj-groovy-dsl.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
JAR=%{buildroot}%{_javadir}/asciidoctorj-groovy-dsl.jar
test -s "$JAR"
CP="$JAR:%{asciidoctorj_jar}:%{_javadir}/asciidoctorj-api.jar:%{jruby_jar}:%{_javadir}/apache-groovy.jar:%{_javadir}/antlr4-runtime.jar"
for extra in \
	%{_javadir}/asm.jar \
	%{_javadir}/asm-commons.jar \
	%{_javadir}/asm-tree.jar \
	%{_javadir}/asm-util.jar \
	%{_javadir}/asm-analysis.jar \
	%{_javadir}/jnr-netdb.jar \
	%{_javadir}/jnr-enxio.jar \
	%{_javadir}/jnr-unixsocket.jar \
	%{_javadir}/jnr-posix.jar \
	%{_javadir}/jnr-constants.jar \
	%{_javadir}/jnr-ffi.jar \
	%{_javadir}/jffi.jar \
	%{_javadir}/joni.jar \
	%{_javadir}/jcodings.jar \
	%{dirgra_jar} \
	%{invokebinder_jar} \
	%{_javadir}/options.jar \
	%{_javadir}/jzlib.jar \
	%{_javadir}/joda-time.jar \
	%{_javadir}/jitescript.jar \
	%{_javadir}/backport9.jar \
	%{_javadir}/crac.jar \
	%{_javadir}/fastdoubleparser.jar \
	%{_javadir}/ant.jar
do
	test -s "$extra"
	CP="$CP:$extra"
done
mkdir -p check
cat > check/GroovyDslCheck.java << 'EOF'
import org.asciidoctor.Asciidoctor;
import org.asciidoctor.Options;
import org.asciidoctor.groovydsl.AsciidoctorExtensions;

public class GroovyDslCheck {
    public static void main(String[] args) {
        Asciidoctor doctor = Asciidoctor.Factory.create();
        AsciidoctorExtensions.extensions(
            "postprocessor { document, output -> output + \"\\nGROOVY_DSL_MARK\" }\n");
        AsciidoctorExtensions.registerTo(doctor);
        String html = doctor.convert("= Hello\n\nworld", Options.builder().standalone(true).build());
        if (html == null || !html.contains("<h1>Hello</h1>") || !html.contains("GROOVY_DSL_MARK")) {
            System.out.println(html);
            throw new RuntimeException("missing mark");
        }
        System.out.println("groovy_dsl_ok GROOVY_DSL_MARK");
        doctor.shutdown();
    }
}
EOF
"$JAVA_HOME/bin/javac" --release 17 -encoding UTF-8 -Xlint:-options -cp "$CP" -d check check/GroovyDslCheck.java
"$JAVA_HOME/bin/java" \
	--enable-native-access=ALL-UNNAMED \
	-Djffi.boot.library.path=%{_libdir} \
	-Djava.library.path=%{_libdir} \
	--add-exports jdk.unsupported/sun.misc=ALL-UNNAMED \
	--add-opens java.base/java.lang=ALL-UNNAMED \
	--add-opens java.base/java.io=ALL-UNNAMED \
	--add-opens java.base/java.util=ALL-UNNAMED \
	--add-opens java.base/sun.nio.ch=ALL-UNNAMED \
	-cp "check:$CP" \
	GroovyDslCheck > check/out.txt
cat check/out.txt
grep -F -qx 'groovy_dsl_ok GROOVY_DSL_MARK' check/out.txt

%files -f .mfiles
%doc README.adoc CHANGELOG.adoc
%license LICENSE.txt
