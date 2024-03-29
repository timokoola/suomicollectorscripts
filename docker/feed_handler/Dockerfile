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
    jsonlines \
    humanize \
    beautifulsoup4 \
    opml \
    feedparser \
    requests \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y curl apt-transport-https ca-certificates gnupg
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-cli -y


# Create a user that does not have root privileges 
ARG username=tkoola
RUN useradd --create-home --home-dir /home/${username} ${username}
ENV HOME /home/${username}

WORKDIR /home/${username}

# Switch to our newly created user
USER ${username}

COPY basic_feeds.opml .
COPY kotus_all.json .
COPY handle_feed_contents.py .

ENTRYPOINT ["python3", "handle_feed_contents.py", "basic_feeds.opml"]

