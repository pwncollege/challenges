PHP exposes URL query parameters through the `$_GET` array.
This application compares `secret` with a string stored in its source before revealing the flag.
Read `/challenge/www/index.php`, satisfy the check, and get the flag.
Run `/challenge/server`, then interact with `http://challenge.localhost/`.
