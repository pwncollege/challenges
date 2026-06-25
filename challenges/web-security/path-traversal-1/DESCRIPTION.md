This level will explore the intersection of Linux path resolution, when done naively, and unexpected web requests from an attacker.
We've implemented a simple web server for you --- it will serve up files from /challenge/files over HTTP.
Can you trick it into giving you the flag?

The webserver program is `/challenge/server`.
You can run it just like any other challenge, then talk to it over HTTP (using a different terminal or a web browser).
We recommend reading through its code to understand what it is doing and to find the weakness!

----
**HINT:**
If you're wondering why your solution isn't working, make sure what you're trying to query is what is actually being received by the server! 
`curl -v [url]` can show you the exact bytes that curl is sending over.
