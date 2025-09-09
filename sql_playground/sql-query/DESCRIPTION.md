This challenge will be the start of your SQL journey.
In this challenge, and throughout this module, we'll use a SQL engine called [SQLite](https://sqlite.org/).
SQLite is an extremely lightweight SQL engine that, rather than using a complex SQL server process to host databases, simply interacts with database files directly.
This makes it very convenient to prototype applications on, and we use it for almost all our SQL needs in the challenges on pwn.college, but you wouldn't want to use it for, say, a production website...
In the challenge file (`/challenge/sql`), you'll notice our use of SQLite via the TemporaryDB class.
Feel free to ignore the inner workings of that class --- we simply use it as a wrapper to execute SQL queries and get results.
Focus on the rest of the code!

This challenge will start with a very simple query.
The query we'll learn is `SELECT`.
You can use `SELECT` to (😎) _select_ data from tables in your databse.
Its basic syntax is `SELECT what FROM where`, where `what` and `where` are things you specify.
The `where`, typically, is a database table, and the `what` are the columns you want the query to fetch.
If you don't want to worry about the column to `SELECT`, you can do `SELECT *`!

Read the code to understand the layout of the database you're querying, and select the flag!

----
**NOTE:**
This challenge, and the other challenges in the series, will try to link to relevant SQLite documentation.
This documentation can be rather dry and dense.
Feel free to use other resources as well.
There are LOTS of SQL guides on the internet: the only reason we made this one is to give an accelerated guide for the parts of SQL learners will need for pwn.college challenges!