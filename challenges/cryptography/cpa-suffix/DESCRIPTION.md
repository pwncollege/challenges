Okay, now let's complicate things slightly to increase the realism.
It's rare that you can just craft queries for the plaintext that you want.
However, it's less rare that you can isolate the _tail end_ of some data into its own block, and in ECB, this is bad news.
We'll explore this concept in this challenge, replacing your ability to query substrings of the flag with just an ability to encrypt some bytes off the end.

Show us that you can still solve this!

----
**HINT:**
Keep in mind that, once you recover some part of the end of the flag, you can build a new codebook with additional prefixes of the known parts, and repeat the attack on the previous byte!
