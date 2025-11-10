Recall how HTTP requests contain fields separated by spaces?
For example: `GET /solve HTTP/1.1`.
What if the path (e.g., instead of `/solve`) has spaces inside it?
This is a reasonable thing to happen, as these paths often reference directories, and directories may have spaces in their names!

Left to their own devices, spaces would mess up the HTTP request.
Consider an HTTP server trying to make sense of `GET /solve my challenge HTTP/1.1`.
A clever server might be able to deal with it, but it's not impossible that a version that simply reads one word at a time would read `my` instead of `HTTP/1.1` and panic!

To avoid such situations, URLs are _encoded_ using [URL Encoding](https://en.wikipedia.org/wiki/Percent-encoding).
This is a simple encoding compared to what you've seen in [Dealing with Data](/fundamentals/data-dealings).
Any tricky characters (such as spaces) are simply hex-encoded, with a `%` plopped in front of them.
Of course, because `%` thus becomes a tricky character in itself, it must also be encoded.
In the above example, `/solve my challenge` would become `/solve%20my%20challenge`, as the hex value of the ASCII space character is `0x20`.

Anyways, now we'll practice.
We stuck spaces in the endpoints.
Can you still get the flag?

----
**INFO:**
You'll find that you need to encode URLs with curl as well (though we won't make you jump through that hoop), in the exact same way.
Python's requests library, however, will automatically urlencode things for you.
So useful!
