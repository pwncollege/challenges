So by using `d`, Alice can encrypt data that (because `n` and `e` are in the public key) anyone can decrypt...
This might seem silly, but it actually enables a capability that we haven't yet seen in the module: the ability to attest to multiple people that a message came from Alice.
This can serve as a sort of cryptographic version of a pen-and-ink signature and, in fact, it is called a _signature_!

This level will explore one application (and pitfall) of RSA signatures.
Recall that `c == m**e mod n`, and recall from middle school that `(x**e)*(y**e) == (x*y)**e`.
This holds just as well in `mod n`, and you can probably see the issue here...

This level gives you a signing oracle.
Go use it to craft a flag command!
