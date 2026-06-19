The previous level's path traversal happened because of a disconnect between:

1. The developer's awareness of the true range of potential input that an attacker might send to their application (e.g., the concept of an attacker sending characters that have special meaning in paths).
2. A gap between the developer's intent (the implementation makes it clear that we only expect files under the `/challenge/files` directory to be served to the user) and the reality of the filesystem (where paths can go "back" up a directory level).

This level tries to stop you from traversing the path, but does it in a way that clearly demonstrates a further lack of the developer's understanding of how tricky paths can truly be.
Can you still traverse it?
