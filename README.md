# Reproducible Builds with YBD Using the Concourse Pipeline

This repo should contain all the required information to set up a
[concourse](http://concourse.ci/) pipeline that uses
[YBD](https://github.com/devcurmudgeon/ybd.git) to build
[Baserock](http://wiki.baserock.org/) systems.

## Setup

- Clone the
[concourse-scripts](https://github.com/perryl/concourse-scripts.git) repo

- (OPTIONAL) Build your own Docker image
  - This requires you have a [Docker hub](http://hub.docker.com/) login and
docker installed on your system
  - Follow the instructions [here](http://doc.docker.com/linux/step_four) and
[here](http://doc.docker.com/linux/step_six)
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

- Navigate [here](http://192.168.100.4:8080/pipelines/ybd-build) and see your
pipeline in action!

## Beginnings of automation

Work is currently being done to find a way to best automate the process of
pipeline creation. In essence, the aim is the following:

`input baserock system -> run script/parser -> generate pipeline per stratum 
 -> set up all stratum pipelines on concourse -> build strata via concourse
 -> build system via concourse ( -> run reproducibility tests on system)`

This can easily be tested by performing the following steps:

- Clone this repo

- Clone Baserock [definitions](
http://git.baserock.org/cgi-bin/cgit.cgi/baserock/baserock/definitions.git/)

- Install vagrant on your system and set up with the following:
```
    vagrant init concourse/lite
    vagrant up
```

- Run the following command:
```
    ./construct-pipelines.sh <path/to/definitions/systems/your-system.morph>
```
  - This will run the parser python script over the given system, outputting a
    separate build YAML for each strata, then setting up a pipeline using each
    YAML file in your concourse system.

- (OPTIONAL) If you just want to view the stratum YAML files without setting up
individual pipelines on concourse, run the following command:
```
    ./parser.py --system=<path/to/definitions/systems/your-system.morph>
```
  - This will just output the individual stratum pipelines to a directory with
    the same name as the system morphology.

## Further features

This pipeline is currently very basic; it simply attempts to build
(successfully as of January 11th 2016, using the 
[perryl/perryl-concourse](https://hub.docker.com/r/perryl/perryl-concourse/)
docker image) build-essential and the `base-system-x86_64-generic` Baserock
system from [definitions](
http://git.baserock.org/cgi-bin/cgit.cgi/baserock/baserock/definitions.git/).

As of now the main concern is getting more visibility of what the build does at
each stage. To do this, the pipeline will be modified into at least two tasks,
one to parse the system in definitions, which will then output a separate YAML
file containing build instructions for each system inside the system.

That is, instead of a single task building the system as a whole, there will
be one task parsing the system, and then separate consecutive tasks building
each item in the system individually.

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
