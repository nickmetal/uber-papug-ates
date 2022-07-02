# context: ../

FROM python:3.10-alpine
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
RUN apk add --update --no-cache gcc libc-dev linux-headers libffi-dev bash bind-tools curl make automake gcc g++ subversion python3-dev

COPY ./task_service/requirements.txt /code/
RUN pip install --use-deprecated=legacy-resolver -r requirements.txt

COPY ./task_service/ ./
COPY ./common_lib ./common_lib
