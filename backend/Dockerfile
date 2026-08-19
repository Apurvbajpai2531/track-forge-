# ---------- Stage 1: builder ----------
FROM python:3.12 AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

RUN echo "Stage 1 is succeed" 

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

RUN echo "Stage 2 is succeed"