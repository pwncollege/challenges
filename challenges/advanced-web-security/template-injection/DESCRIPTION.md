# Template Injection

Templates sit between application data and executable presentation logic.
When an application treats user input as template source, the template language decides what that input can reach.

This module moves across engines with very different security models: restricted data lookup, callable methods, template loaders, file inclusion, and embedded general-purpose code.
The later challenges return to Jinja with progressively tighter input rules, then combine prototype pollution with a Nunjucks template sink.

For each challenge, inspect the service, identify the engine and its available context, and use the smallest capability that reaches the flag.
