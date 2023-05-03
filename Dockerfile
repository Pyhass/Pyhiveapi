FROM python:latest

WORKDIR /apps
COPY hive_configs.json .
RUN git clone https://github.com/StephenGrey/Pyhiveapi.git
RUN cd Pyhiveapi && git fetch origin
RUN cd Pyhiveapi && git merge
RUN pip install -r Pyhiveapi/requirements.txt
RUN pip install influxdb_client
RUN pip install /apps/Pyhiveapi
CMD python /apps/Pyhiveapi/auto_poll.py /apps/hive_configs.json


# cd /apps/Pyhiveapi && python auto_poll.py hive_configs.json
#cd /code/Pyhiveapi
#CMD python /apps/Pyhiveapi/auto_poll.py hive_configs.json
#
#

