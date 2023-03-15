FROM python:latest

WORKDIR /apps
RUN git clone https://github.com/StephenGrey/Pyhiveapi.git
RUN pip install -r Pyhiveapi/requirements.txt
RUN pip install influxdb_client


#TO TEST SOURCECODE:
#pip install /code/pyhiveapi
#cd /code/Pyhiveapi
#python auto_poll.py hive_configs.json
#
#