You need to install ComfyUI manually - there is no current nixos package or flake for that.
Then python won't see the stdcc++ library and nvidia drivers.
Then copy shell.nix to ComfyUI folder and start a nix shell: nix-shell
It will use the shell.nix as a hook (will execute the content) which will ~create symlinks so that python sees the necessary libraries in /usr/lib folder (although they are in some nixos store).
Then run source comfy-env/bin/activate and finally:
python ComfyUI/main.py

At the time of writing this making this shell.nix part of the global configuration.nix didn't work. You had to use LD_LIBRARY as a session variable in configuration.nix which was causing system crashes...oh well, that's the linux fun.
Cheers.
