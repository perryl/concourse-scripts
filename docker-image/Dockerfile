FROM debian:jessie

RUN apt-get update && \
      apt-get install -y python build-essential gawk git m4 wget sudo

RUN  wget https://bootstrap.pypa.io/get-pip.py && \
      python get-pip.py
RUN pip install pyyaml sandboxlib jsonschema bottle cherrypy requests
