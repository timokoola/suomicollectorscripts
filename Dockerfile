FROM ubuntu

# Run the following commands as super user (root):
USER root

ENV DEBIAN_FRONTEND=noninteractive 

# Install required packages for notebooks
RUN apt-get update && apt-get install -y python3-pip libvoikko-dev python-libvoikko voikko-fi wget && pip install --upgrade pip && pip install \
       jupyter \
       metakernel \
       zmq \
       libvoikko \
       requests \
     && rm -rf /var/lib/apt/lists/*

# Create a user that does not have root privileges 
ARG username=tkoola
RUN useradd --create-home --home-dir /home/${username} ${username}
ENV HOME /home/${username}

WORKDIR /home/${username}

# Create the configuration file for jupyter and set owner
RUN echo "c.NotebookApp.ip = '*'" > jupyter_notebook_config.py && chown ${username} *

# Switch to our newly created user
USER ${username}

# Allow incoming connections on port 8888
EXPOSE 8888

COPY book_to_wordforms.py .
COPY kotus_all.json .


CMD ["python3", "book_to_wordforms.py"]
# CMD ["jupyter", "notebook"]
# CMD ["/bin/bash"]
