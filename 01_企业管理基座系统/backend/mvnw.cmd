@REM Maven Wrapper script for Windows
@REM ----------------------------------------------------------------------------
@if "%DEBUG%"=="" @echo off
@REM Set local scope for the variables with windows NT shell
if "%OS%"=="Windows_NT" setlocal
set DIRNAME=%~dp0
if "%DIRNAME%"=="" set DIRNAME=.
@REM Resolve any "." and ".." in APP_HOME to make it shorter.
for %%i in ("%DIRNAME%") do set APP_HOME=%%~fi
set APP_HOME=%APP_HOME:~0,-1%
set WRAPPER_JAR="%APP_HOME%\.mvn\wrapper\maven-wrapper.jar"
set WRAPPER_LAUNCHER=org.apache.maven.wrapper.MavenWrapperMain
set WRAPPER_URL="https://repo.maven.apache.org/maven2/org/apache/maven/wrapper/maven-wrapper/3.2.0/maven-wrapper-3.2.0.jar"
if exist %WRAPPER_JAR% (
    goto run
)
powershell -Command "&{"^
		"$webclient = new-object System.Net.WebClient;"^
		"$webclient.DownloadFile('%WRAPPER_URL%', '%WRAPPER_JAR%')"^
		"}"
:run
"%JAVA_HOME%\bin\java.exe" -jar %WRAPPER_JAR% %MAVEN_CONFIG% %*
if "%OS%"=="Windows_NT" endlocal
