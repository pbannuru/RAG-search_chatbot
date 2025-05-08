# FROM harbor.ext.hp.com/knowledge_search/python:3.12 AS build

# WORKDIR /app
# COPY requirements.txt .
# RUN python -m venv /opt/env
# RUN . /opt/env/bin/activate && pip install --no-cache-dir -r requirements.txt

# # Stage 2: Runtime
# FROM harbor.ext.hp.com/knowledge_search/python:3.12 AS runtime
# WORKDIR /app
# COPY --from=build /app /app
# COPY . .
# COPY --from=build /opt /opt
# # RUN apk add --no-cache libpq

# CMD . /opt/env/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8090




FROM harbor.ext.hp.com/knowledge_search/python:3.12 AS build

# Update package list and install system dependencies with updates
RUN apt-get update && apt-get upgrade -y --no-install-recommends

# Set up the working directory
WORKDIR /app

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN python -m venv /opt/env
RUN . /opt/env/bin/activate && \
    pip install --no-cache-dir --disable-pip-version-check -r requirements.txt --no-deps

# Stage 2: Runtime
FROM harbor.ext.hp.com/knowledge_search/python:3.12 AS runtime

# Update package list and install necessary dependencies
RUN apt-get update && apt-get upgrade -y --no-install-recommends

# Set up the working directory
WORKDIR /app

# Copy the build environment from the build stage
COPY --from=build /app /app
COPY . .

# Copy Python environment from the build stage
COPY --from=build /opt /opt

# Command to run the application
CMD . /opt/env/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8090
