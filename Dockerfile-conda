FROM continuumio/conda-ci-linux-64-python3.8
USER root
COPY . /app/
RUN conda install -c anaconda tensorflow=2.2.0 pip
RUN pip install -r /app/requirements.txt
EXPOSE 5000
WORKDIR /app
ENTRYPOINT ["python3","app.py"]