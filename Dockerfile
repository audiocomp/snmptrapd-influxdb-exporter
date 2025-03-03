# Builder stage
FROM python:3.13-alpine3.21 AS builder
LABEL maintainer="Steve Brown https://github.com/audiocomp"

# Update base image and install dependencies
RUN apk update && apk upgrade --no-cache -v && apk add --no-cache -v net-snmp-libs libcap

# Update PIP and install required packages
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

# Grant the application the capability to bind to privileged ports
RUN setcap 'cap_net_bind_service=+ep' /usr/local/bin/python3.13

# Copy application code
COPY ./snmptrapd_influxdb_exporter /app

# Final stage
FROM python:3.13-alpine3.21
LABEL maintainer="Steve Brown https://github.com/audiocomp"

# Update base image
RUN apk update && apk upgrade --no-cache -v

# Create a non-root user and group
RUN addgroup -g 1501 -S appgroup && adduser -u 1501 -D -H -S appuser -G appgroup

# Copy net-snmp-libs from builder stage
COPY --from=builder /usr/lib /usr/lib
COPY --from=builder /usr/share/snmp /usr/share/snmp

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /app /app

# Change ownership of the application files
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

WORKDIR /app

EXPOSE 162/udp

CMD ["python3", "snmptrapd-influxdb-exporter.py"]
