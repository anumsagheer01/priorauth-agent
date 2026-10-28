FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-cloud.txt ./
# Cloud deps are REQUIRED for a real review: google-adk, BigQuery, Storage.
# A container built from requirements.txt alone would report adk_available=False
# and fail real reviews (2026-10-27 audit finding). Streamlit is NOT started
# by this container; it serves FastAPI only on port 8000. Run Streamlit
# separately with PRIORAUTH_API_URL=<service URL> if a UI demo is wanted.
RUN pip install --no-cache-dir -r requirements.txt -r requirements-cloud.txt
COPY src ./src
COPY data ./data
COPY app ./app
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["uvicorn", "priorauth.api:app", "--host", "0.0.0.0", "--port", "8000"]
