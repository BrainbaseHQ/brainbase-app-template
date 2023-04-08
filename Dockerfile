FROM python:3.9
LABEL maintainer="egrigokhan@gmail.com"
COPY . /app
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r app/src/requirements.txt
ENV PYTHONPATH=/app/app/src:$PYTHONPATH
EXPOSE 8080
ENTRYPOINT ["python"]
CMD ["app/app.py"]
