FROM harbor.ext.hp.com/knowledge_search/python:3.12 AS build

WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/env
RUN . /opt/env/bin/activate && pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM harbor.ext.hp.com/knowledge_search/python:3.12 AS runtime
WORKDIR /app
COPY --from=build /app /app
COPY . .
COPY --from=build /opt /opt
# RUN apk add --no-cache libpq

CMD . /opt/env/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8


