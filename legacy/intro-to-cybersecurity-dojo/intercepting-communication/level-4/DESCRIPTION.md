From your host at 10.0.0.1, connect to some unknown remote host on the 10.0.0.0/16 subnet, on port 31337.

Now our network is starting to get bigger!
There are 65,536 possible hosts on this subnet, so finding the remote host manually would really be a real pain.
Even a basic `for` loop processing 10 hosts per second would take over an hour to complete!

We can of course get fancier with our shell scripting (parallelizing, etc.), but for now, let's consider a standard tool designed to help with this kind of task: `nmap`.

`nmap` is a powerful network scanning tool that can be used to discover hosts and services on a computer network.
You can, for example, scan for which hosts are up (and popular services running on those hosts) on 10.0.0.0/30 with the following command:

```sh
nmap 10.0.0.0/30
```
Within 15 seconds or so, you should see that your host at 10.0.0.1 is up, as expected.

When conducting a network scan, it is important to be aware of the potential impact on the network.
Under default settings, `nmap` tries to be at least somewhat polite and not totally overwhelm a network with tons of packets.
Nevertheless, it is still possible to cause network congestion or even trigger security alerts by running a network scan, and so it is important to be aware of the potential impact.
As such, you shouldn't run a network scan on a network that you don't own or have permission to scan!

In this network, it's okay to be a little more aggressive, a little more "rude" with our scanning.
You'll want to review the man page for `nmap` (`man nmap`) to see how you can speed up the scanning process: you're specifically interested in how many packets are being sent per second.
Disabling some of the default scans, such as DNS resolution, can also speed up the scanning process.
When in doubt, use `-v` to see a bit more information about what `nmap` is currently doing.
