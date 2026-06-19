You're not going to believe this, but... a Padding Oracle Attack doesn't just let you decrypt arbitrary messages: it lets you _encrypt_ arbitrary data as well!
This sounds too wild to be true, but it is.
Think about it: you demonstrated the ability to modify bytes in a block by messing with the previous block's ciphertext.
Unfortunately, this will make the previous block decrypt to garbage.
But is that so bad?
You can use a padding oracle attack to recover the exact values of this garbage, and mess with the block before that to fix this garbage plaintext to be valid data!
Keep going, and you can craft fully controlled, arbitrarily long messages, all without knowing the key!
When you get to the IV, just treat it as a ciphertext block (e.g., plop a fake IV in front of it and decrypt it as usual) and keep going!
Incredible.

Now, you have the knowledge you need to get the flag for this challenge.
Go forth and forge your message!

----
**FUN FACT:**
Though the Padding Oracle Attack was [discovered](https://www.iacr.org/archive/eurocrypt2002/23320530/cbc02_e02d.pdf) in 2002, it wasn't until 2010 that researchers [figured out this arbitrary encryption ability](https://static.usenix.org/events/woot10/tech/full_papers/Rizzo.pdf).
Imagine how vulnerable the web was for those 8 years!
Unfortunately, padding oracle attacks are _still_ a problem.
Padding Oracle vulnerabilities come up every few months in web infrastructure, with the latest (as of time of writing) [just a few weeks ago](https://www.cvedetails.com/cve/CVE-2024-45384/)!
