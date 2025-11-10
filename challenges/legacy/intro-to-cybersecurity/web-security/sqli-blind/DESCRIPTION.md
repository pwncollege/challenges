SQL injection happen in all sorts of places in an application and, like command injections, sometimes the result of the query is not sent back to you.
With command injections, this case is easier: the commandline is so powerful that you can do a lot of things even blindly.
With SQL injections, this is sometimes not the case.
For example, unlike some other databases, the SQLite database used in this module cannot access the filesystem, execute commands, and so on.

So, if the application does not show you the data resulting from your SQL injection, how do you actually leak the data?
Sometimes, even if the actual data is not shown, you can recover one bit!
If the result of a query can make the application act two different ways (say, redirecting to an "Authentication Success" page versus an "Authentication Failure" page), then an attacker can carefully craft yes/no questions that they can get answers to.

This challenge gives you exactly this scenario.
Can you leak the flag?
