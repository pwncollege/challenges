Tornado templates compile to Python and support statement tags as well as output expressions.
Among those statements is module import, so the template can reach libraries that were never placed in its data context.

The report service stores its flag in a SQLite database after startup.
Use Tornado's template language to retrieve it.
