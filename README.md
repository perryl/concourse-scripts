# Reproducible Builds with YBD Using the Concourse Pipeline

This repo should contain all the required information to set up a [concourse](http://concourse.ci/)
pipeline that uses [YBD](https://github.com/devcurmudgeon/ybd.git) to build [Baserock](http://wiki.baserock.org/) systems.

## Setup

- Clone the [concourse-scripts](https://github.com/perryl/concourse-scripts.git) repo

- (OPTIONAL) Build your own Docker image
  - This requires you have a [Docker hub](http://hub.docker.com/) login and docker installed on your
    system
  - Follow the instructions [here](http://doc.docker.com/linux/step_four) and [here](http://doc.docker.com/linux/step_six)
  - Replace the perryl/perryl-concourse docker image in build.yml with your own
    docker hub image

- Install vagrant on your system

- Run the following from the concourse-scripts repo directory:
```
    vagrant init concourse/lite
    vagrant up
    fly set-pipeline -p ybd-build -c build.yml
    fly unpause-pipeline -p ybd-build
```

- Navigate [here](http://192.168.100.4:8080/pipelines/ybd-build) and see your pipeline in action!

## Further features

This pipeline is currently very basic; it simply attempts to build
(successfully as of January 11th 2016, using the 
[perryl/perryl-concourse](https://hub.docker.com/r/perryl/perryl-concourse/) docker image) build-essential and the Baserock
base-system from [definitions](http://git.baserock.org/cgi-bin/cgit.cgi/baserock/baserock/definitions.git/).

The eventual aim of this is to be able to build all systems in Baserock
definitions with ease and once completed, run tests on the resulting artifacts.
I will be looking at artifact reproducibility in particular; output successful
system build artifacts, obtain the shasum of each, and store somewhere. Then,
once the system is triggered to build again, perform the same test, compare
against previous shasums (should they exist), then output that information to
the user.

The outputted data should be easily readable by anyone wishing to view the
results, rather than listing every unreproducible artifact and giving the
viewer data overload in the form of a series of long text files. If we can get
an output that says `System X: Y% reproducible`, with an option to detail
unreproducible components separately should the viewer so desire, this would
be a success.
