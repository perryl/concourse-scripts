# concourse-scripts

This repo should hopefully contain all the required scripts to set up a
concourse pipeline that utilises YBD to build a system, then run a test script
to check the resulting artifacts for reproducibility, by checking the shasum
of each artifact between consecutive builds.

The outputted data should be easily readable by anyone wishing to view the
results, rather than listing every unreproducible artifact and giving the
viewer too much data to parse.
