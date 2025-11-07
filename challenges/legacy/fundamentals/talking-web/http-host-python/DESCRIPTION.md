Unfortunately, most of the modern internet runs on the infrastructure of a handful of companies, and a given server run by these companies might be responsible for serving up websites for dozens of different domain names.
How does the server decide which website to serve?
The `Host` header.

The `Host` header is a _request_ header sent by the client (e.g., browser, curl, etc), typically equal to the domain name entered in the HTTP request.
When you go to `https://pwn.college`, your browser automatically sets the `Host` header to `pwn.college`, and thus our server knows to give you the `pwn.college` website, rather than something else.

Until now, the challenges you've been interacting with have been `Host`-agnostic.
Now they start checking.
Set the right `Host` header and get the flag!
