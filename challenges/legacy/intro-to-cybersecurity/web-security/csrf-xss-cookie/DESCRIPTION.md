Okay, now that you have the CSRF-to-XSS chain figured out, pull off a CSRF leading to an XSS leading to a cookie leak that'll allow you to log in and get the flag!

----
**HINT:**
Your solution might have two levels of JavaScript: one that runs on your `http://hacker.localhost:1337` page, and one that runs in the reflected XSS.
We suggest testing the latter first, by manually triggering the page with that input and seeing the result.
Furthermore, as this code might be complex, be VERY careful about URL encoding.
For example, `+` will _not_ be encoded to `%2b` by most URL encoders, but _it is a special character in a URL_ and gets decoded to a space (` `).
Needless to say, if you use `+` in your JavaScript, this can lead to complete havoc.
