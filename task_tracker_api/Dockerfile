FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

ENV PYTHONPATH "${PYTHONPATH}:/"
ENV PORT=8000

RUN pip install --upgrade pip

COPY ./requirements.txt /app/
COPY ./register_routes.sh /app/

RUN pip install -r requirements.txt 
RUN apt install curl

COPY ./app /app
EXPOSE 7777
CMD ["uvicorn", "app.main:app", "--workers", "1", "--host", "0.0.0.0", "--port", "7777", "--log-level", "debug"]
