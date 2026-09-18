You have forged a forwarded client address before, through a proxy that failed to replace it.
Here there is no proxy at all.
The application was written to sit behind one, so it reads `X-Forwarded-For` and believes whatever it finds there.
Its admin page is restricted to a single address, which it names when it turns you away.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
