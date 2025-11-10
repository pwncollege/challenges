Now, the hard part begins...
Oftentimes, what you need to exfiltrate is other data accessible to your JavaScript on the website, but you often have to make HTTP requests to retrieve it.
In modern JavaScript, HTTP requests are made using the `fetch()` function.
It works roughly as follows:

```javascript
fetch("http://google.com").then(response => response.text()).then(website_content => ???);
```

The `???`, of course, is the code that you want to execute on the website contents.
This API looks so absolutely insane because JavaScript is insane, but also because it actually has a hard problem to solve.
It has to execute logic in an environment where network errors, CPU load, laptop suspending and resuming, firewalls, and other crazy things can interfere with the loading and operation of the resources that it depends on.
The above code uses JavaScript "promises", which is a complex programming pattern that lets you write logic that _will_ be executed on data that is not _yet_ available, when that data finally does become available.
The `.then()` is the part of the promise that specifies what will be eventually executed.
Here, the flow is roughly as follows:

1. `fetch()` returns a promise and starts to fetch `http://google.com`.
   This might take a while, might never succeed, or might succeed immediately.
   At any rate, it initially returns a `promise` object that has a `then()` member function that will run when the response is available.
2. The response becomes available and the promised code executes.
   This code takes the promised response and calls `response.text()`, which retrieves the _full_ text contents returned by `http://google.com`.
   Because this might take a while to load fully, this _also_ returns a promise, and _that_ promise also has a `.then()` method that we can specify code for.
3. Finally, all the content is available and our final promised code runs.
   This can be anything, but for most of our purposes, this is where we exfiltrate our data like you did in previous challenges.

This can be insanely hard to understand and debug.
Please be ready to debug this in Firefox in practice mode.

In this level, the flag is no longer nicely wrapped in JavaScript.
It's just boring old text.
You'll need to fetch it and exfiltrate it to score.
Good luck!
