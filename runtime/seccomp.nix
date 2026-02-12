{ pkgs, name }:
let
  seccompBaseProfile = pkgs.fetchurl {
    # Pin the upstream Docker seccomp base profile so nix builds stay reproducible.
    url = "https://raw.githubusercontent.com/moby/profiles/9fb516320ad275f544b4995f424dfa8b6261cffa/seccomp/default.json";
    hash = "sha256-AVNvHR35OK5hHrog1jSeDeepm27N7hVJQnoLAbgwHig=";
  };

  seccompProfileScript = pkgs.writeText "${name}-seccomp.py" ''
    import json
    import sys

    READ_IMPLIES_EXEC = 0x0400000
    ADDR_NO_RANDOMIZE = 0x0040000

    with open(sys.argv[1]) as profile_file:
        seccomp = json.load(profile_file)

    existing_personality_values = []
    for syscalls in seccomp["syscalls"]:
        if "personality" not in syscalls["names"]:
            continue
        if syscalls["action"] != "SCMP_ACT_ALLOW":
            continue
        assert len(syscalls["args"]) == 1
        arg = syscalls["args"][0]
        assert list(arg.keys()) == ["index", "value", "op"]
        assert arg["index"] == 0, arg
        assert arg["op"] == "SCMP_CMP_EQ"
        existing_personality_values.append(arg["value"])

    new_personality_values = []
    for new_flag in [READ_IMPLIES_EXEC, ADDR_NO_RANDOMIZE]:
        for value in [0, *existing_personality_values]:
            new_value = value | new_flag
            if new_value not in existing_personality_values:
                new_personality_values.append(new_value)
                existing_personality_values.append(new_value)

    for new_value in new_personality_values:
        seccomp["syscalls"].append(
            {
                "names": ["personality"],
                "action": "SCMP_ACT_ALLOW",
                "args": [{"index": 0, "value": new_value, "op": "SCMP_CMP_EQ"}],
            }
        )

    with open(sys.argv[2], "w") as out_file:
        json.dump(seccomp, out_file)
  '';
in
pkgs.runCommand "${name}-seccomp.json" { nativeBuildInputs = [ pkgs.python3 ]; } ''
  python ${seccompProfileScript} ${seccompBaseProfile} "$out"
''
