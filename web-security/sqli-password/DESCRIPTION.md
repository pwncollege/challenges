The previous level's SQL injection was quite simple to pull off and still have a valid SQL query.
This was, in part, because your injection happened at the very end of the query.
In this level, however, your injection happens partway through, and there is (a bit) more of the SQL query afterwards.
This complicates matters, because the query must remain valid despite your injection.
