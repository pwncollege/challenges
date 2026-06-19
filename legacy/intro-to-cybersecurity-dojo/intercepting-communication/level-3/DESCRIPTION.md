From your host at 10.0.0.1, connect to some unknown remote host on the 10.0.0.0/24 subnet, on port 31337.

Fortunately, there are only 256 possible hosts on this subnet, so you can just try them all!

One simple tool that you can use to help you with this is `ping`.
If you "ping" a host, and it is up, you will get a response; otherwise, ping will timeout and warn you that it cannot reach the host.

For example, try pinging yourself:
```sh
ping 10.0.0.1
```
This will continuously keep pinging until you press `Ctrl-C` to stop it.

You can also try pinging a host that you know is down:
```sh
timeout 10 ping 10.0.0.2
```
This will run ping for (up to) 10 seconds, but you should see ping messages indicating that the host is unreachable before the timeout.

As with most commands, you can also run `man ping` to see the manual page for `ping`.

Consider this an opportunity to practice your shell scripting skills!
You can of course ping each of the 256 hosts manually, but maybe a `for` loop might be even easier!

```sh
for i in $(seq 10); do
  echo $i
done
```
