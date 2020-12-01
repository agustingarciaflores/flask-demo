FROM python
WORKDIR /app
ADD app/ requirements.txt /app
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]