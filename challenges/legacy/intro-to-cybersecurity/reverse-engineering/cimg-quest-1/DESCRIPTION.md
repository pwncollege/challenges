Another goal of reverse engineering is for _interoperability_.
Time is a harsh mistress, and many things can happen to or around software as time goes on.
For example, source code [can get lost](https://www.rockpapershotgun.com/square-enix-digital-preservation-plans-slowed-by-lost-code), as it is typically secretive and internal to a company in question, but binary files tend to persist, as they are widely (e.g., commercially) distributed.
When source code is lost, interoperability must be achieved by reverse engineering the binary file to either [reconstruct](https://decompilation.wiki/applications/program-reconstruction/) or [adapt](https://scanlime.org/2009/04/a-binary-patch-for-robot-odyssey/) them.

In this challenge, we've recovered the source code of the game `The Epic Quest for the Flag` (`/challenge/quest.py`), but its customized cIMG-based graphics engine is missing!
We've provided you a close approximation (a normal cIMG parser in `/challenge/cimg`), but it does not work out of the box.
You'll need to binary-patch it for compatibility!
Can you uncover the flag?

----
**NOTE:**
Note, `/challenge/quest.py` uses `cimg` as a graphics engine, but it's built for a custom version of `cimg` that you do not have.
You run it with `/challenge/quest.py NOFLAG | /challenge/cimg` to run it in "compatibility mode": no flag, but compatible with the standard `cimg`.
If you want the flag, you'll need to modify the `cimg` to work with the `quest`, and run it via `/challenge/quest.py | /home/hacker/your-patched-cimg`.

----
**HINT:**
You can either patch using your reverse engineering tool of choice or figure out the file address of the bytes you want to patch and use `hexedit`.
