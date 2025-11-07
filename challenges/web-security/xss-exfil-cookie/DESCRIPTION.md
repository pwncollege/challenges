Depending on the attacker's goals, what they might actually be after is the victim's entire account.
For example, attackers might use XSS to exfiltrate victim authentication data and then use this data to take over the victim's account.

Authentication data is often stored via browser cookies, such as what happened in `Authentication Bypass 2` (but, typically, much more secure).
If an attacker can leak these cookies, the result can be disastrous for the victim.

This level stores the authentication data for the logged in user in a cookie.
You must use XSS to leak this cookie so that you can, in turn, use it in a request to impersonate the `admin` user.
This exfiltration will happen over HTTP to a server that you run, and everything you need is available via JavaScript's `fetch()` and its ability to access (some) site cookies.

----
**HINT:**
By "server that you run", we really mean that listening on a port with `nc` will be sufficient.
Look at the `-l` and `-v` options to `nc`.
