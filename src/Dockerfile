FROM python:3.11-slim

WORKDIR /app

COPY . /app


# Установка curl
RUN apt-get update && apt-get install -y curl

# Установка Google Chrome
RUN curl -LO  https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
RUN rm google-chrome-stable_current_amd64.deb

# Check chrome version
RUN echo "Chrome: " && google-chrome --version

RUN pip install -r config/requirements.txt

EXPOSE 8079

CMD ["python", "parser_main.py"]