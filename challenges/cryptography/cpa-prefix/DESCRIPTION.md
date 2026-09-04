Okay, now let's complicate things slightly.
It's not so common that you can just chop off the end of interesting data and go wild.
However, _much_ more common is the ability to _prepend_ chosen plaintext to a secret before it's encrypted.
If you carefully craft the prepended data so that it _pushes_ the end of the secret into a new block, you've just successfully isolated it, accomplishing the same as if you were chopping it off!

Go ahead and do that in this challenge.
The core attack is the same as before, it just involves more data massaging.

----
**HINT:**
Keep in mind that a typical pwn.college flag is somewhere upwards of 50 bytes long.
This is four blocks (three full and one partial), and the length can vary slightly.
You will need to experiment with how many bytes you must prepend to push even one of the end characters to its own block.

**HINT:**
Keep in mind that blocks are 16 bytes long!
After you leak the last 16 bytes, you'll be looking at the second-to-last block, and so on.
