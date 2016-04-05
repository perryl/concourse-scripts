FROM debian:jessie

RUN sed -i 's/^deb.*main$/& contrib/' /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y build-essential git gawk m4 wget linux-user-chroot \
    python-setuptools python-cherrypy python-requests python-jsonschema \
    python-fs python-yaml python-bottle

ENV HOME /root
WORKDIR $HOME
RUN git clone http://github.com/CodethinkLabs/sandboxlib sandboxlib
WORKDIR sandboxlib
RUN python ./setup.py install
WORKDIR $HOME
RUN rm -r sandboxlib
