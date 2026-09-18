You have selected a virtual host by authority before.
The `Host` header is not tied to DNS, and not tied to where your connection actually landed: it is free text that the client asserts.
This service answers for exactly one authority, and it names that authority when you get it wrong.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
