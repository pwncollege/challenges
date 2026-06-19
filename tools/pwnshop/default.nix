{ pkgs, pwn-workspace-runtime }:

pkgs.python3Packages.buildPythonApplication {
  pname = "pwnshop";
  version = "0.0.0";
  pyproject = true;

  src = pkgs.lib.fileset.toSource {
    root = ./.;
    fileset = pkgs.lib.fileset.unions [
      ./pyproject.toml
      ./src/pwnshop
    ];
  };

  build-system = [
    pkgs.python3Packages.setuptools
  ];

  dependencies = with pkgs.python3Packages; [
    black
    click
    jinja2
    pyyaml
    requests
    rich
  ];

  makeWrapperArgs = [
    "--prefix"
    "PATH"
    ":"
    (pkgs.lib.makeBinPath (
      with pkgs;
      [
        clang-tools
        docker
        git
      ]
    ))
    "--set-default"
    "PWN_WORKSPACE"
    "${pwn-workspace-runtime}"
  ];
}
