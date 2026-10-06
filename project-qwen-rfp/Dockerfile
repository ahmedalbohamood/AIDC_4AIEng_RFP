# Stage 1: build the frontend from source so a deploy never depends on a
# manually pre-built, possibly-stale dist/ sitting on disk.
FROM node:22-slim AS frontend-build
WORKDIR /app
COPY ["AI RFP System Interface (1)/", "./"]
RUN corepack enable && corepack prepare pnpm@10.34.3 --activate \
    && pnpm install --frozen-lockfile
# Backend serves this build from the same origin, so API calls must be
# relative (""), not the dev default of http://localhost:8420.
ENV VITE_API_BASE_URL=""
RUN pnpm build

FROM python:3.10-slim

WORKDIR /app

COPY project-qwen-rfp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi "uvicorn[standard]" python-multipart prometheus-fastapi-instrumentator

COPY project-qwen-rfp/rfpbench/ ./rfpbench/
COPY project-qwen-rfp/server.py .
COPY --from=frontend-build /app/dist/ ./frontend_dist/

EXPOSE 8420
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8420"]
