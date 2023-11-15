FROM python:3.11-alpine3.18
LABEL maintainer="Steve Brown https://github.com/audiocomp"

# Update SSL
RUN apk add --no-cache --progress -v openssl

# Update PIP
RUN apk add --no-cache --progress -v py3-pip

# Install Required Packages
COPY requirements.txt  /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Add Code & Config
COPY ./snmptrapd_influxdb_exporter/mibs /mibs
COPY ./snmptrapd_influxdb_exporter/models /models
COPY ./snmptrapd_influxdb_exporter/modules /modules
ADD ./snmptrapd_influxdb_exporter/snmptrapd-influxdb-exporter.py .
ADD ./snmptrapd_influxdb_exporter/config.yaml .
ADD README.md .

EXPOSE 162/udp

CMD ["python3","snmptrapd-influxdb-exporter.py"]
