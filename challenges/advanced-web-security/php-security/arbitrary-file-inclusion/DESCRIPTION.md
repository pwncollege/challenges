PHP's `include` evaluates PHP code in the selected file and outputs content outside PHP tags.
Letting a request choose that file gives the requester control over what the application includes.
This application selects a page through the `page` URL parameter.
Use it to recover the flag.
Run `/challenge/server`, then interact with `http://challenge.localhost/`.
