# KN_Builder

Fetch and parse source files to construct the KnowEnG Knowledge Network

The main objective for this repository is to collect community datasets curating annotations of and interactions between genes and proteins and transform them into a comprehensive, heterogeneous network, called the ‘Knowledge Network’ (KN). This Knowledge Network will assist researchers to understand their experimental genomic data spreadsheets through network-based machine learning and graph mining tools developed by KnowEnG. To do this, we created a library of parsers to convert inconsistent public source data formats into standard network representations while preserving the provenance and relevant metadata. This repository incorporates those parsers into an automated and containerized build pipeline that can run to produce current, versioned databases of the Knowledge Network.

# Documentation
The most complete documentation can be found [here](http://knowredis.knoweng.org/).

You can find the tools that simply running the build pipeline [here](https://github.com/KnowEnG/KnowNet_Pipeline_Tools).

