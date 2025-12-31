FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY utilities/sheets_app/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY utilities/sheets_app utilities/sheets_app

EXPOSE 8000

CMD ["uvicorn", "utilities.sheets_app.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
