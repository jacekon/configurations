{ pkgs ? import <nixpkgs> { config.allowUnfree = true; } }:

let
  # The libraries your pip packages (torch, etc.) need to see
  libraries = with pkgs; [
    stdenv.cc.cc.lib      # Fixes libstdc++.so.6 error
    zlib                  # Common dependency
    glib                  # Common dependency
    libGL                 # Fixes some graphical issues
    libGLU
    linuxPackages.nvidia_x11 # The NVIDIA driver libraries
  ];
in
pkgs.mkShell {
  packages = [
    pkgs.python3
    pkgs.cudaPackages.cudatoolkit # Helps if torch needs generic cuda libs
  ];

  # This runs every time you enter the shell
  shellHook = ''
    # 1. Add the Nix packages above to LD_LIBRARY_PATH
    export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath libraries}:$LD_LIBRARY_PATH

    # 2. Add the dynamic /run/opengl-driver path (CRITICAL for GPU detection)
    export LD_LIBRARY_PATH=/run/opengl-driver/lib:/run/opengl-driver-32/lib:$LD_LIBRARY_PATH

    echo "NixOS Environment Loaded: GPU and C++ libs are ready."
  '';
}
