{
  description = "pwn.college challenges dev env";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      lib = nixpkgs.lib;
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: lib.genAttrs systems (system: f system);
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          pwnChallengeRuntime = import ./runtime { inherit pkgs lib; };
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              git
              jq
              docker
              pwnChallengeRuntime
            ];
            shellHook = ''
              export DOCKER_HOST="$(sudo ${pwnChallengeRuntime}/bin/pwn-challenge-runtime)"
            '';
          };
        });
    };
}
