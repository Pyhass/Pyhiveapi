#Put configs into a json file - these will be copied into the container
#Launch by specifying the config file
#e.g. docker run -it -e CONFIG="hive_configs2.json" -t IMAGETAG


FROM python:latest
WORKDIR /apps
COPY *.json .
RUN git clone https://github.com/StephenGrey/Pyhiveapi.git
RUN cd Pyhiveapi && git fetch origin
RUN cd Pyhiveapi && git merge
RUN pip install -r Pyhiveapi/requirements.txt
RUN pip install influxdb_client
RUN pip install /apps/Pyhiveapi
#CMD ls /apps
#CMD echo “Loading configs from : $CONFIG” 
CMD python /apps/Pyhiveapi/auto_poll.py /apps/$CONFIG


# cd /apps/Pyhiveapi && python auto_poll.py hive_configs.json
#cd /code/Pyhiveapi
#CMD python /apps/Pyhiveapi/auto_poll.py hive_configs.json
#
#936
#
#RUN is an image build step, the state of the container after a RUN command will be committed to the container image. A #Dockerfile can have many RUN steps that layer on top of one another to build the image.

#CMD is the command the container executes by default when you launch the built image. A #Dockerfile will only use the final CMD defined. The CMD can be overridden when starting a container with docker run $image $other_command.

