* Each host represent a machine
    * It could be a linux system that is reachable via SSH
    * It could be a docker container inside a linux system that is reachable via SSH
    * Each host has a unique id
* Each compartment lives inside a host
    * A host can have many compartment, each have different name
    * compartment name are globally unique within a 

* Purpose of the staging area: if this is a docker host, any file copied to container will be staged here, and then copied to the container
Filesystem structure
```
${MORDOR_ROOT}
|
+-- bin
|
+-- stage
|
+-- compartments
      |
      +-- compartment1
      |     |
      |     +-- deployment1
      |     |
      |     +-- deployment2
      |
      +-- compartment2
            |
            +-- deployment1
            |
            +-- deployment2
```

When a host is initialized by a host, it always has a file /etc/mordor.json, which tells the mordor configuration.
If we found this file, we will assume mordor has been initialized. Otherwise, we will initialize mordor.