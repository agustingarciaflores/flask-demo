FROM python:alpine
WORKDIR /app
ADD app.py requirements.txt /app
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "app.py"]