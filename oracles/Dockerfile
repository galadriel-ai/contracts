FROM python:3.10
WORKDIR /app
COPY . .
COPY sidekik.json /app/sidekik.json
RUN pip install -r requirements_non_enclave.txt
CMD ["python", "oracle.py"]