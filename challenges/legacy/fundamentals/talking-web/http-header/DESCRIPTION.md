HTTP facilitates the transfer of both _data_ (e.g., the HTML that `/challenge/server` sends you) and _metadata_ (data about the data).
The latter is sent via _headers_: fields in an HTTP request or response that give additional instructions to the server or browser.
In this case, the flag is in a header.
Can you find it?

----
**HINT:** you can inspect headers using Firefox's Web Developer Tools (≡, then `More Tools`).
The Network tab of the tools displays all of the HTTP connections (you might need to reload the page after opening the Web Developer Tools for the connection to show up).
Each of these connections has a `Headers` subtab, which shows headers that your browser sent alongside its request (`Request Headers`) and the headers that it received alongside the response (`Response Headers`).
Find the flag header there!
