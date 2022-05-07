FROM python:3.10-alpine
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN apk add --update --no-cache gcc libc-dev linux-headers libffi-dev bash bind-tools curl
RUN pip install -r requirements.txt
RUN wget -P /code https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh && chmod +x /code/wait-for-it.sh
COPY . /code/
