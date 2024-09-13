FROM python:3.9

RUN pip install --upgrade pip

RUN apt-get update && \
    apt-get install -y wkhtmltopdf

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./cenit_services /app

WORKDIR /app

COPY ./entrypoint.sh /

ENTRYPOINT ["sh", "/entrypoint.sh"]