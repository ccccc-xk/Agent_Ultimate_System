FROM eclipse-temurin:17-jre-jammy

WORKDIR /app

# Copy Maven wrapper and pom.xml
COPY backend/.mvn ./.mvn
COPY backend/mvnw.cmd ./
COPY backend/pom.xml ./

# Copy source code
COPY backend/src ./src

# Build
RUN apt-get update && apt-get install -y maven && rm -rf /var/lib/apt/lists/*
RUN mvn clean package -DskipTests -f pom.xml

EXPOSE ${PORT:-9001}

CMD ["java", "-jar", "target/enterprise-base-1.0.0.jar"]
