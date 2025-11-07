You've been staring at web server code all this time and figuring out how to speak to it.
Now, let's learn to _listen_.

In this level, you will write a simple server that'll receive the request for the flag!
Simply copy the server code from, say, the very first module, remove anything extra, and build a web server that'll listen on port 1337 (instead of 80 --- you can't listen on port 80 as a non-administrative user) and on hostname `localhost`.
When you're ready, run `/challenge/client`, and it will launch an internal web browser and visit `http://localhost:1337/` with the flag!
