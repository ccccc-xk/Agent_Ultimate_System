FROM eclipse-temurin:17-jdk-jammy

WORKDIR /app

# Copy backend source (Chinese path handled by Docker Linux)
COPY "01_企业管理基座系统/backend/pom.xml" ./
COPY "01_企业管理基座系统/backend/src" ./src

# Build
RUN apt-get update && apt-get install -y maven && rm -rf /var/lib/apt/lists/*
RUN mvn clean package -DskipTests

EXPOSE ${PORT:-9001}

CMD ["java", "-jar", "target/enterprise-base-1.0.0.jar"]
