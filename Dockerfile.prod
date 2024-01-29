FROM python:3.10.13-alpine

WORKDIR /usr/src/api

# prevent python from writing .pyc file
ENV PYTHONDONTWRITEBYTECODE 1
# ensure that python output send to terminal without buffering
ENV PYTHONUNBUFFERED 1 

RUN pip install --upgrade pip 
COPY ./requirements.txt /usr/src/api/requirements.txt 
RUN pip install -r requirements.txt

COPY ./entrypoint.sh /usr/src/api/entrypoint.sh 
COPY . /usr/src/api/

ENTRYPOINT [ "/usr/src/api/entrypoint.sh" ]

