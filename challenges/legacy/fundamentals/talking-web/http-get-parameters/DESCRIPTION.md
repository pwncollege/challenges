Like a function call in a programming language or a command execution on the shell, HTTP requests can include _parameters_.
GET requests send parameters alongside the path in the URL, in a part of the URL called the [Query String](https://en.wikipedia.org/wiki/Query_string).
In this challenge, you'll learn how to craft this query string.
Read the challenge source to understand what parameter you need, and send it over!
You can use any client you want: the process is basically the same in all of them.

----
**SECURITY NOTE:**
It's tempting to think of HTTP parameters as similar to parameters to a function call.
However, keep in mind: when you're writing C or Python or Java code, an attacker (typically) can't just call random functions in your program with random parameters.
But with HTTP, they _can_.
They can just make HTTP requests wherever they want!
This has caused quite a few security issues...
