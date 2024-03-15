FROM python:3.10-alpine
WORKDIR .
COPY . .
RUN pip install -r requirements_non_enclave.txt
CMD ["python", "oracle.py"]