Once an attacker has code execution inside a victim's browser, they can do a lot of things.
You've made a `GET` request in your previous attack, but typically, it's the `POST` requests that will change application state.
This challenge ratchets up the realism: the `/publish` now needs a `POST` request.
Luckily, `fetch` supports this!

Go figure out how to `POST`, and get the flag.
