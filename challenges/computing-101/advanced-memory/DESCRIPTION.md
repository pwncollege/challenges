Wow, you are a budding x86 assembly programmer!
You've set registers, triggered system calls, and wrote your first program that cleanly exits.
Now, we have one more big concept for you: _memory_.

You, as (presumably) a human being, have [Short Term Memory](https://en.wikipedia.org/wiki/Short-term_memory) and [Long Term Memory](https://en.wikipedia.org/wiki/Long-term_memory).
When performing specific computation, your brain loads information you've previously learned into your short term memory, then acts on that information, then eventually puts new resulting information into your long-term memory.
Societally, we also invented other, longer-term forms of storage: oral histories, journals, books, and wikipedia.
If there's not enough space in your long-term memory for some information, or the information is not important to commit to long-term memory, you can always go and look it up on wikipedia, have your brain stick it into long-term memory, and pull it into your short-term memory when you need it later.

This multi-level hierarchy of information access from "small but accessible" (your short term memory, which is right there when you need it but [only stores 5 to 9 pieces of information](https://www.simplypsychology.org/short-term-memory.html) to "large but slow" (remembering stuff from your massive long-term memory) to "massive but absolutely glacial" (looking stuff up on wikipedia) is actually the foundation of the [Memory Hierarchy](https://en.wikipedia.org/wiki/Memory_hierarchy) of modern computing.
We've already learned about the "small but accessible" part of this in the previous module: those are registers, limited but FAST.

More spacious than even all the registers put together, but much much MUCH slower to access, is computer memory, and this is what we'll dig into with this module, giving you a glimpse into another level of the memory hierarchy.
