Advanced users often prefer connecting over a remote shell.
In order to ssh into your challenge instances, you must link a public ssh key to your account [through your settings](/settings#ssh-key).
You can quickly generate an ssh key by running `ssh-keygen -f key -N ''` in a terminal on your (unix-friendly) host machine.
This will generate files `key` and `key.pub`, which are your private and public keys respectively.
Once you have linked your *public* ssh key to your account, you can connect to the dojo over ssh with `ssh -i key hacker@dojo.pwn.college`.
