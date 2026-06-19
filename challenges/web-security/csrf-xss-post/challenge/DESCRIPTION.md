This level closes the loophole that allowed you to steal cookies from JavaScript.
Cookies have a special setting called `httponly`, and when this is set, the cookie is _only_ accessible in HTTP headers, and not through JavaScript.
This is a security measure, aimed to prevent exactly the type of cookie pilfering that you have been doing.
Luckily, Flask's default `session` cookie is set to be `httponly`, so you cannot steal it from JavaScript.

So, now how would you get the flag with your CSRF-to-XSS shenanigans?
Luckily, you don't _need_ the cookie!
Once you have JavaScript execution within the page, you can freely `fetch()` other pages without worrying about the Same Origin Policy, since you now live in the same Origin.
Use this, read the page with the flag, and win!

----
**DEBUGGING:**
Break the chain into pieces.
First, load the reflected XSS URL directly and confirm that the JavaScript runs inside `challenge.localhost`.
Then serve your attacker page and confirm that it sends the victim to that exact URL with the encoding intact.
Finally, use Firefox's Network tab or your listener logs to confirm that the injected JavaScript makes the outbound request you expect.
