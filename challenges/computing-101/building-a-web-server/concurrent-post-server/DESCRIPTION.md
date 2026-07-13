Expanding your server’s capabilities further, this challenge focuses on handling HTTP POST requests concurrently.
POST requests are more complex because they include both headers and a message body.
You will once again use [fork](https://man7.org/linux/man-pages/man2/fork.2.html) to manage multiple connections, while using [read](https://man7.org/linux/man-pages/man2/read.2.html) to capture the entire request.
Again, you will parse the URL path to determine the specified file, but this time instead of reading from that file, you will instead write to it with the incoming POST data.
In order to do so, you must determine the length of the incoming POST data.
The *obvious* way to do this is to parse the `Content-Length` header, which specifies exactly that.
Alternatively, consider using the return value of [read](https://man7.org/linux/man-pages/man2/read.2.html) to determine the total length of the request, parsing the request to find the total length of the headers (which end with `\r\n\r\n`), and using that difference to determine the length of the body--this seemingly more complicated algorithm may actually be easier to implement.
Finally, return just a `200 OK` response to the client to indicate that the POST request was successful.
