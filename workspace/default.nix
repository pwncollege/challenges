{
  pkgs,
  lib ? pkgs.lib,
}:

let
  mkRuntime =
    {
      packageProfile ? "minimal",
      code ? false,
      desktop ? false,
    }:
    let
      workspacePackages =
        if packageProfile == "minimal" then
          import ./runtime/packages { inherit pkgs; }
        else if packageProfile == "extended" then
          import ./runtime/packages/extended.nix { inherit pkgs desktop; }
        else
          throw "unsupported PWN_WORKSPACE_PACKAGES=${packageProfile}; expected minimal or extended";

      runtimeServices = import ./runtime/services {
        inherit
          pkgs
          code
          desktop
          workspacePackages
          ;
      };
      serviceNames = [ "terminal" ] ++ lib.optional code "code" ++ lib.optional desktop "desktop";
      serviceProfile = lib.concatStringsSep "-" serviceNames;
      name =
        if packageProfile == "minimal" && serviceProfile == "terminal" then
          "pwn-workspace-runtime"
        else
          "pwn-workspace-runtime-${packageProfile}-${serviceProfile}";
      runtime = import ./runtime {
        inherit
          pkgs
          name
          workspacePackages
          runtimeServices
          ;
      };
    in
    {
      inherit runtime;
      summary = "packages=${packageProfile} services=${lib.concatStringsSep "," serviceNames}";
    };
in
{
  inherit mkRuntime;

  mkActivator =
    runtime:
    {
      egressDomains ? [ "example.com" ],
      publicKey ? null,
      volumeBasePath ? null,
    }:
    import ./activate.nix {
      inherit
        pkgs
        lib
        egressDomains
        publicKey
        volumeBasePath
        ;
      workspaceRuntime = runtime.runtime;
    };

  workspaceDaemon = import ./platform/daemon/package.nix { inherit pkgs; };
}
