Specifying multiple HTTP parameters in curl is a bit of a special case, because `&` means something special in the shell (it launches a command in the background), and if you're not careful, the shell will trip over your `&`!
Make sure to put the whole URL, including the query string, in quotes to avoid this situation.
Try that now.
