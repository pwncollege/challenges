Awesome, you got the hang of the basic process.
There's one more thing you need to do, though: you must read and understand the source code of the challenge!
Web servers _route_ HTTP requests to different _endpoints_: `http://challenge.localhost/pwn` might go to the endpoint that handles the request path `/pwn`, and `http://challenge.localhost/college` might go to the endpoint that handles the request path `college`.
This challenge has a randomly-chosen endpoint name.
You must read the code in `/challenge/server`, understand it, and figure out which endpoint to visit in the browser!

----
Confused?
Our web servers are implemented using the [flask](https://flask.palletsprojects.com/en/stable/quickstart/) library.
Read their documentation to build up understanding of the code, or experiment with it!
