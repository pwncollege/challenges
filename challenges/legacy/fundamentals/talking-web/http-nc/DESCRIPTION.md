You've learned how to HTTP (though, of course, you've probably been HTTPing for most of your life!).
Now, let's learn how to _really_ HTTP.
The HTTP protocol itself, as in the exact data that is sent over the network, is actually surprisingly human-readable and human-writable.
In this challenge, you'll learn to write it.
This challenge requires you to use a program called "netcat" (command name: `nc`), which is a simple program that communicates over a network connection.
Netcat's basic usage involves two arguments: the _hostname_ (where the server is listening on, such as www.google.com for Google), and the port (the standard HTTP port is 80).

When it starts up, netcat connects to the server and gives you a raw channel to communicate with it.
You'll be talking _directly with the web server_, with no intermediary!
How cool is that?

Recall the lectures, find the format of an HTTP request, and make a GET request to the `/` endpoint (we'll do more endpoints later) to get the flag!

----
**HINT:**
Can't tell if netcat is connecting or not?
Use the `-v` flag to turn on some verbosity!

**HINT:**
Typed your GET request and nothing happens after you hit Enter?
HTTP requests are terminated by _two_ newlines.
Try hitting Enter again!

**A thought...**
Until this moment, have you ever truly HTTPed?
