Of course, the previous spoofing worked because you know the source port that the client was using, and were thus able to forge the server's response.
This was, in fact, at the core of a [very famous vulnerability](https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=0c1e863b6698808b724def8793d7cba023494808) in the [Domain Name System](https://en.wikipedia.org/wiki/Domain_Name_System) that facilitates the translation of host names like `https://pwn.college` to the appropriate IP addresses.
The vulnerability allowed attackers to forge responses from DNS servers and redirect victims to IP addresses of their choice!

The fix for that vulnerability was to randomize the source port that DNS requests go out from.
Likewise, this challenge no longer binds the source port to 31338.
Can you still force the response?

----

**HINT:**
The source port is only set once per socket, whether at bind time or at the first `sendto`.
What do you do when there's a fixed number that you don't know?
