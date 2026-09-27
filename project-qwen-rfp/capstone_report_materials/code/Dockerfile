FROM python:3.10-slim

WORKDIR /app

COPY project-qwen-rfp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi "uvicorn[standard]" python-multipart prometheus-fastapi-instrumentator

COPY project-qwen-rfp/rfpbench/ ./rfpbench/
COPY project-qwen-rfp/server.py .
COPY ["AI RFP System Interface (1)/dist/", "./frontend_dist/"]

EXPOSE 8420
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8420"]
