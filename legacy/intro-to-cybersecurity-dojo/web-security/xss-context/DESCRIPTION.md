Like with SQL injection and command injection, sometimes your XSS occurs in the middle of some non-optimal context.
In SQL, you have dealt with injecting into the middle of quotes.
In XSS, you often inject into, for example, a textarea, as in this challenge.
Normally, text in a textarea is just, well, text that'll show up in a textbox on the page.
Can you bust out of this context and `alert("PWNED")`?

As before, the `/challenge/victim` of this challenge takes a URL argument on the commandline, and it will visit that URL.
