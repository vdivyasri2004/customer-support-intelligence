FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python3 -c 'from app.core.database import engine, Base; from app.models.user import User; from app.models.dataset import Dataset; from app.models.ticket import Ticket; from app.models.analysis import Analysis; Base.metadata.create_all(bind=engine)' && python3 seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
