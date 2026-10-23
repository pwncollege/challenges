The upload handler now rejects filenames ending in `.php`.
Compare its filename check with the web server's handler configuration, and find a filename they interpret differently.
Upload a file that recovers the flag.
Run `/challenge/server`, then interact with `http://challenge.localhost/`.
