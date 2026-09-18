The same disagreement, with the preferences swapped: the firewall frames the body by `Transfer-Encoding`, the application by `Content-Length`.
Now the firewall consumes your entire chunked body, while the application stops after the byte count you declared and reads whatever is left as the next request.
The firewall still refuses to pass `/admin`.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
