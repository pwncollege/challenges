Let's start putting a few things together...
A CSRF can lead to many things, including other injections!
Use the CSRF in this level to trigger a XSS and invoke an `alert("PWNED")` somewhere in `http://challenge.localhost`!

----
**HINT:**
You will likely want to use JavaScript on your `http://hacker.localhost:1337` page to send a `GET` request with `<script>` tags in a URL parameter.
Be careful: if you encode this JavaScript in your HTML, your `<script>` tag will have the word `</script>` in a string (the URL parameter).
This string `</script>` will actually be parsed by your browser as the closing tag of your page's actual `<script>` tag, and all hell will break loose.

If you encounter this error, I recommend dynamically building that string (e.g., `"</s"+"cript>"`) in the JavaScript that runs on `http://hacker.localhost:1337`.
