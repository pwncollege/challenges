There is a fairly wide gap between the features that TCP provides and UDP's barebones nature.
Sometimes, developers want _some_ of those features, and end up reimplementing just those that they need on top of UDP.
This leads to weird situations, such as the ability to trigger outbound traffic to other servers, with a potential application to Denial of Service [amplification](https://www.cisa.gov/news-events/alerts/2014/01/17/udp-based-amplification-attacks).

Rather than leaking the flag directly, this challenge allows you to redirect it to another server.
Can you catch it on the other side?

----

**HINT:**
You'll need to either use a UDP server to actually receive the flag (e.g., python or netcat), or just sniff it off the network with Wireshark when it comes to you, even if you don't have a server listening!
