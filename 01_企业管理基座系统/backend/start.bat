@echo off
chcp 65001 >nul
set JAVA_HOME=D:\Program Files\Java\jdk-17
set JAR=target\enterprise-base-1.0.0.jar

:restart
echo [%date% %time%] Starting backend...
"%JAVA_HOME%\bin\java.exe" -jar %JAR%
echo [%date% %time%] Backend stopped, restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto restart
