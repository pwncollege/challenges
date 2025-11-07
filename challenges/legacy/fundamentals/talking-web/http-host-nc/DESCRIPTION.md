And, finally, you can learn how Hosts are _actually_ sent over the network in netcat.
This might be a bit trickier.
You can actually use `curl` as a source of information here!
Curl's `-v` option causes it to print out the exact headers it's sending over (and the ones it receives!).
Observe it, copy that with netcat, and get the flag!
