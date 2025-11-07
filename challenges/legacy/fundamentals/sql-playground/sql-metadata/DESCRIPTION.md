In actual security scenarios, there are times where the attacker lacks certain information, such as the names of tables that they want to query!
Luckily, every SQL engine has some way to query _metadata_ about tables (though, confusingly, every engine does this differently!).
SQLite uses a special `sqlite_master` table, in which it stores information about all other tables.
Can you figure out the name of the table that contains the flag, and query it?
