FROM docker.elastic.co/elasticsearch/elasticsearch:8.13.0

# Copy pre-downloaded IK plugin and install
COPY ik.zip /tmp/ik.zip
RUN elasticsearch-plugin install -b file:///tmp/ik.zip; rm -f /tmp/ik.zip || true
