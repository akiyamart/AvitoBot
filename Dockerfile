FROM python:3.11-slim

WORKDIR /app

COPY src/config/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8080

CMD ["python", "manager.py"]