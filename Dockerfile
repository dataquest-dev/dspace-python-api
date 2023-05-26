FROM python:latest
WORKDIR /

COPY . ./pyimport/
WORKDIR /pyimport/

RUN pip install -r requirements.txt
CMD [ "python", "./dspace_import.py", "docker"]
