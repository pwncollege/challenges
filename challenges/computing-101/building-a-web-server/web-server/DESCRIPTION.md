In the final challenge, your server must support both concurrent GET and concurrent POST requests within a single program.
The checker will send a randomized mix of the two request types, so each accepted connection must fork a child that handles whichever request arrived.
For a GET request, return the requested file contents as in the previous GET levels.
For a POST request, write the request body to the requested path and return `200 OK` as in the previous POST level.
After completing this, you will have built a simple, but fully functional, web server capable of handling both request types.
