FROM python:3.12-slim
WORKDIR /opt/project/apps/api
COPY apps/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api/data.py apps/api/main.py apps/api/auth.py apps/api/login_throttle.py apps/api/audit_store.py ./
COPY apps/api/migrations/ ./migrations/
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
