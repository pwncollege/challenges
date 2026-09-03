Removing `.` and `..` segments can change the resource identified by a path.
Some clients remove those segments before transmission; make sure the server receives the path you intended.
With `curl`, `--path-as-is` preserves them.
Reach the normalized flag route.
Run `/challenge/server`, then interact with it at `http://challenge.localhost/`.
