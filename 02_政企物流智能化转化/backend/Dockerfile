FROM eclipse-temurin:17-jre-jammy

WORKDIR /app

COPY target/smart-logistics-1.0.0.jar app.jar

EXPOSE ${PORT:-9002}

CMD ["java", "-jar", "app.jar"]
