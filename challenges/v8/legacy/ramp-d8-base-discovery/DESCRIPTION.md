A process-memory primitive becomes more useful after you locate stable process images.
One common first step is scanning page-aligned addresses backward from a leaked pointer until an ELF header appears.

In this level, the harness gives you an absolute read function and one leaked process pointer.
Find the modeled d8 base address and return it from `solve(api)`, then run `/challenge/run` with your solve file to get the flag.
