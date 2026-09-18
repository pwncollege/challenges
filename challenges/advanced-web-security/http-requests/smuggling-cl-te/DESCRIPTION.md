A firewall and the application behind it read the same bytes from the same connection, so they must agree on where one request ends and the next begins.
Two headers can answer that question.
`Content-Length` counts the bytes of the body; `Transfer-Encoding: chunked` frames the body as sized chunks that end with a zero-length chunk.
Send both, and the answer depends on which header each server prefers.
When the firewall prefers `Content-Length` and the application prefers `Transfer-Encoding`, the firewall sees one request where the application sees two.
The bytes the firewall counted as part of your body, the application reads as a request of its own, and that request passed no filter.
The firewall here refuses to pass `/admin`, and the application serves the flag there.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
