Actual XSS exploits try to achieve something more than `alert("PWNED")`.
A very common goal is to use the ability to execute JavaScript inside a victim's browser to initiate new HTTP requests masquerading as the victim.
This can be done in a number of ways, including using JavaScript's `fetch()` function.

This challenge implements a more complex application, and you will need to retrieve the flag out of the `admin` user's unpublished draft post.
After XSS-injecting the `admin`, you must use the injection to make an HTTP request (as the `admin` user) to enable you to read the flag.
Good luck!

----
**DEBUGGING:**
This level adds an additional bit of complexity to the injected script: the `fetch()`.
Now, three things can go wrong:

1. The `<script>` HTML injection.
   Again, verify that using View Source or Inspect Element in the DOJO's Firefox.
   Log in as `guest` (or modify the script so that you can log in as `admin` in practice mode) and play around graphically.
2. The JavaScript itself.
   Verify this by checking Firefox's JavaScript console for errors and by using print-debugging (to the Firefox console by doing `console.log`).
3. The GET request that you'll trigger using `fetch()` or whatnot.
   You can, again, debug this in Firefox by looking at the Network tab of the Web Developer Tools.
   Have the tab open, trigger your attack, and see what's happening with the actual request.
