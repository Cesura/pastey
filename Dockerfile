FROM tensorflow/tensorflow:2.9.1
ENV PASTEY_WORKERS=2
ENV PASTEY_THREADS=4
ENV PASTEY_LISTEN_PORT=5000
RUN mkdir -p /app/data
COPY requirements.txt /app/
RUN pip install -U pip setuptools wheel
RUN pip install -r /app/requirements.txt
COPY . /app/
WORKDIR /app
RUN pip install gunicorn
ENTRYPOINT ["sh", "-c", "gunicorn -w $PASTEY_WORKERS -t $PASTEY_THREADS -b :$PASTEY_LISTEN_PORT --worker-class=gthread app:app"]
