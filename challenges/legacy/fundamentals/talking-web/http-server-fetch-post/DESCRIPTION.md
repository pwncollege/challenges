And, naturally, we can use `fetch()` to make POST requests.
This lets our JavaScript pretend to submit forms and so on, which is pretty neat!
Let's practice that in this level.
You can look up how to pass advanced arguments to `fetch()` on your own, but we'll give you some hints for some things that _should_ appear in your JavaScript verbatim:

- `{`
- `method: "POST"`
- `body`
- `new URLSearchParams`
- `}`

Good luck!

----
**NOTE:**
There are many ways to send POST parameters.
In this module, we covered the sending of form data, but other types exist as well, and all have different ways of accessing them via flask.
Make sure you're sending form data in your POST, not something else; otherwise, our server (the way it's implemented) won't see it!
