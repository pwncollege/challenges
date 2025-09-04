# pwncollege challenge monorepo

This repository will one day contain all core pwn.college challenges.

The basic idea is that challenges are just directories in here, similar to how they're specified in dojos currently.
They'll be auto-built out of these directories, probably as docker files (though some nix stuff is another possibility), and deployed seamlessly.

## In the meantime, some musings:

- we need to figure out complex setup scenarios (e.g., compilation, source removal, etc). I'm leaning toward is just requiring a Dockerfile if you want anything other than "all files get copied to /challenge".
- also thinking of requiring a Dockerfile if you want your challenge built on some exotic architecture or something. This might need more thought, but is not a usecase we need to worry about currently.
- all testcases will run with the docker images built. Tests would run in docker containers (or in a dojo deployment)
- with the above, pwnshop's job would shift to being the client-side dojo builder/pusher. I think this will make it significantly smaller and easier to understand
- i have some doubts that this challenges-are-jinja-templates style will scale to all challenge complexities. yan85 has some hella spaghetti code. Maybe refactors will help, or maybe we'll need to have some other workarounds.
