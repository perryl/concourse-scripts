FROM debian:jessie

RUN apt-get update && \
  apt-get install -y python build-essential gawk git m4 wget sudo \
  python-dev python-pip libyaml-dev libxml2-dev libxslt-dev

RUN  wget https://bootstrap.pypa.io/get-pip.py && \
  python get-pip.py
RUN pip install pyyaml jsonschema bottle cherrypy requests
RUN git clone http://github.com/CodethinkLabs/sandboxlib sandboxlib
WORKDIR sandboxlib
RUN python ./setup.py install
WORKDIR $HOME
RUN rm -r sandboxlib
