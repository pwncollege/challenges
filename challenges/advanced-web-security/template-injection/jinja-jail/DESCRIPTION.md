Jinja does not place Python's file and process functions directly in a template context.
Its built-in helper objects are still Python objects, though, and Python functions retain references to the global namespace where they were defined.

Follow that object graph from the template environment to recover the flag.
