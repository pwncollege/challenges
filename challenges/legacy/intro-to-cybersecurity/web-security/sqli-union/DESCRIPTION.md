If you recall, your command injection exploits typically caused _additional_ commands to be executed.
So far, your SQL injections have simply modified the conditions of existing SQL queries.
However, similar to how the shell has ways to chain commands (e.g., `;`, `|`, etc), some SQL queries can be chained as well!

An attacker's ability to chain SQL queries has extremely powerful potential.
For example, it allows the attacker to query completely unintended tables or completely unintended fields in tables, and leads to the types of massive data disclosures that you read about on the news.

This level will require you to figure out how to chain SQL queries in order to leak data.
Good luck!
