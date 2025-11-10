You've followed redirects --- now make one happen!
Have your webserver redirect `/challenge/client` to the right location in `/challenge/server`.
You'll need three terminal windows for this:

1. The first terminal window runs `/challenge/server`, which listens on port 80 and prepares to give the flag.
2. The second terminal window runs your webserver implementation, which listens on port 1337 and prepares to redirect the client.
3. The third terminal window runs `/challenge/client`.

It's complex, but you can do it!
