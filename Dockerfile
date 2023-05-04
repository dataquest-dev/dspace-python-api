FROM python:latest
CMD [ "curl", "http://host.docker.internal:8080/server/api/core/items"]
WORKDIR /

# todo add here parameters, passwords, data location... option to erase database? but we'd need password for that :/
# todo with active input
# parameters needed:
# all in const?
# data location



COPY . ./pyimport/
WORKDIR /pyimport/

RUN pip install -r requirements.txt
#CMD [ "python", "./dspace_import.py", "docker"]
CMD [ "python", "./test.py", "docker"]