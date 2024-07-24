# Python Dockerfile
FROM python:3.9-slim

WORKDIR /usr/src/app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    build-essential \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV LD_LIBRARY_PATH=/usr/lib

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && python -c "import flask; print(flask.__version__)"

# Assuming UID 1001 for myuser in Node.js Dockerfile
RUN groupadd -g 1001 appgroup && \
    useradd -r -u 1001 -g appgroup myuser
USER myuser

COPY src/ .

CMD ["python", "start_websocket.py", "&", "python", "api.py"]
