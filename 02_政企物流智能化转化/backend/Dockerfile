FROM eclipse-temurin:17-jdk-jammy

WORKDIR /app

COPY pom.xml ./
COPY src ./src

RUN apt-get update && apt-get install -y maven && rm -rf /var/lib/apt/lists/*
RUN mvn clean package -DskipTests

EXPOSE 9002

CMD ["java", "-jar", "target/smart-logistics-1.0.0.jar"]
