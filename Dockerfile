FROM tensorflow/tensorflow:2.9.1
WORKDIR /app
COPY requirements.txt /app
RUN mkdir -p /app/data && pip install -r /app/requirements.txt
COPY . /app/
EXPOSE 5000
ENV PASTEY_DATA_DIRECTORY=/app/data  
ENTRYPOINT ["python3", "app.py"]
