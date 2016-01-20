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
  - Replace the perryl/perryl-concourse docker image in parser.py with your own
    docker hub image

- Install vagrant on your system, or ensure it is up-to-date

- Clone Baserock [definitions](
http://git.baserock.org/cgi-bin/cgit.cgi/baserock/baserock/definitions.git/)
or, if you have cloned definitions already, ensure it is up-to-date.

## Pipeline automation

Originally, we had a pipeline that would clone YBD, definitions and
concourse-scripts, then run a shell script containing instructions to run
YBD over the build-essential stratum and base-system-x86_64-generic system.

However, this didn't give us a good output of what was happening at each stage.
If base-system was built inside a single job and failed for some reason, we
wouldn't be able to tell where or why the failure occurred. Instead, what we
needed was a way to visualise the whole system build. In essence, we wanted the
following:

`input baserock system -> run script/parser -> generate pipeline per stratum 
 -> set up all stratum pipelines on concourse -> set resources for each strata
job as chunks -> build strata via concourse -> build system via concourse ( ->
 run reproducibility tests on system)`

Although we do not yet have testing functionality, the full pipeline for a
system can now be shown using the following commands (assuming the instructions
from 'Setup' in this document have been followed):

- Run the following from the concourse-scripts repo directory:
```
    vagrant init concourse/lite
    vagrant up
    ./construct-pipelines.sh <path/to/definitions/systems/your-system.morph>
```
  - This will run the parser python script over the given system, outputting a
    build YAML containing jobs and resources defined by the strata in the
    system, and finally setting up a pipeline using each YAML file in your concourse system.

- (OPTIONAL) If you just want to view the system YAML file without setting up
the pipeline on concourse, run the following command:
```
    ./parser.py --system=<path/to/definitions/systems/your-system.morph>
```

- Congratulations! Your pipeline should now be visible [here](
http://192.168.100.4:8080)

## Further features

This pipeline currently only has the ability to create a single pipeline from a
system passed to the parser by the user. It cannot create single stratum or
clusters-of-systems pipelines right now, nor do we have the ability to
automatically add testing scripts once the system build has finished. For
multiple systems, the user will have to run `./construct-pipelines.sh` for each
system in question.

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
