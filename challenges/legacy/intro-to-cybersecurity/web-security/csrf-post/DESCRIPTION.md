Recall that requests that originate from JavaScript run into the Same-Origin Policy, which slightly complicated our CSRF in the previous level.
You figured out how to make a `GET` request without JavaScript.
Can you do the same for `POST`?

Recall that a typical `POST` request is a result of either a JavaScript-invoked request (no good for SOP) or an HTML form submission.
You'll need to do the latter.
Of course, the `/challenge/victim` won't click the `Submit` button for you --- you'll have to figure out how to do that yourself (HINT: JavaScript can click that button; the request will still count as originating from the form!).

Go `POST`-CSRF to the flag!
