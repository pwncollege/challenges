Though we didn't explore this for TCP, in addition to selecting the destination port, both TCP and UDP can set their _source_ port.
We'll practice that here --- you can set the source port with `s.bind` on the socket, exactly how a server does it to set their listening port.
Read the source code of `/challenge/run` to see what source port you'll need!

----

**NOTE:**
You must set the source port _before_ sending data!
Otherwise, Linux will pick a random source port (the default behavior, when `bind` is not called).
