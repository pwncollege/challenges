Once an attacker has code execution inside a victim's browser, they can do a lot of things.
You've made a `GET` request in your previous attack, but typically, it's the `POST` requests that will change application state.
This challenge ratchets up the realism: the `/publish` now needs a `POST` request.
Luckily, `fetch` supports this!

Go figure out how to `POST`, and get the flag.

----
**DEBUGGING TIPS:**
The debugging path is the same as the previous level, but isolate the `POST` request while you work.
Open Firefox's console and Network tab, trigger your injected script, and confirm that the browser sends a `POST` to `/publish`.
If no request appears, debug the HTML injection and JavaScript first.
If the request appears with the wrong method or target, focus on the `fetch()` options.
