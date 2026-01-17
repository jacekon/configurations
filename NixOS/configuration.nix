# Edit this configuration file to define what should be installed on
# your system.  Help is available in the configuration.nix(5) man page
# and in the NixOS manual (accessible by running ‘nixos-help’).

{ config, pkgs, ... }:

{
  imports =
    [ # Include the results of the hardware scan.
      ./hardware-configuration.nix
    ];

  # Bootloader.
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  #added by Jacek: to detect PWM devices (fans)
  boot.kernelModules = [ "it87" ];
  #added by Jacek: first two: to fix the wifi issue. third to: detect fans to PWM them.
  boot.extraModprobeConfig = ''
  	options rtw89_pci disable_clkreq=y disable_aspm_l1=y disable_aspm_l1ss=y
  	options rtw89_core disable_ps_mode=y
	options it87 force_id=0x8628 ignore_resource_conflict=1
  	'';
  boot.kernelParams = [ "acpi_enforce_resources=lax" ];

  networking.hostName = "nixos"; # Define your hostname.

  # Configure network proxy if necessary
  # networking.proxy.default = "http://user:password@proxy:port/";
  # networking.proxy.noProxy = "127.0.0.1,localhost,internal.domain";

  networking.networkmanager.enable = true;

  # Set your time zone.
  time.timeZone = "Europe/Berlin";

  # Select internationalisation properties.
  i18n.defaultLocale = "en_US.UTF-8";

  i18n.extraLocaleSettings = {
    LC_ADDRESS = "de_DE.UTF-8";
    LC_IDENTIFICATION = "de_DE.UTF-8";
    LC_MEASUREMENT = "de_DE.UTF-8";
    LC_MONETARY = "de_DE.UTF-8";
    LC_NAME = "de_DE.UTF-8";
    LC_NUMERIC = "de_DE.UTF-8";
    LC_PAPER = "de_DE.UTF-8";
    LC_TELEPHONE = "de_DE.UTF-8";
    LC_TIME = "de_DE.UTF-8";
  };

  # Enable the X11 windowing system.
  services.xserver.enable = true;

  # Enable the GNOME Desktop Environment.
  services.xserver.displayManager.gdm.enable = true;
  services.xserver.desktopManager.gnome.enable = true;

  # Configure keymap in X11
  services.xserver.xkb = {
    layout = "us";
    variant = "";
  };

  # Enable CUPS to print documents.
  services.printing.enable = true;

  # Enable sound with pipewire.
  services.pulseaudio.enable = false;
  security.rtkit.enable = true;
  services.pipewire = {
    enable = true;
    alsa.enable = true;
    alsa.support32Bit = true;
    pulse.enable = true;
    # If you want to use JACK applications, uncomment this
    #jack.enable = true;

    # use the example session manager (no others are packaged yet so this is enabled by default,
    # no need to redefine it in your config for now)
    #media-session.enable = true;
  };

  # Enable touchpad support (enabled default in most desktopManager).
  # services.xserver.libinput.enable = true;

  # Define a user account. Don't forget to set a password with ‘passwd’.
  users.users.jacek = {
    isNormalUser = true;
    description = "Jacek";
    extraGroups = [ "networkmanager" "wheel" ];
    packages = with pkgs; [
    #  thunderbird
    ];
  };

  system.autoUpgrade.enable = true;
  system.autoUpgrade.allowReboot = true;

  #added by jacek to fix pytorch not seeing nvidia gpu and libstd++.cc.6 libararies (which are located in /usr/lib on standard linux system) 
  programs.nix-ld.enable = true;
  programs.nix-ld.libraries = with pkgs; [ 
	linuxPackages.nvidia_x11 
	stdenv.cc.cc.lib
	zlib
	glib
	libGL
	libGLU
  ];

  # Allow unfree packages (e.g. Nvidia drivers)
  nixpkgs.config.allowUnfree = true;

  # List packages installed in system profile. To search, run:
  # $ nix search wget
  environment.systemPackages = with pkgs; [
     vim #Nano is  also installed by default.
     wget 
     git 
     ollama # added by Jacek to be replaced by the service below
     mangohud # for fps display 
     protonup
     lutris
     toybox #lspci etc.
     brave #web browser
     dconf #app to manage keyboard shortcuts
     nix-index # for finding files like this one:
     cudaPackages.cudatoolkit     
     cudaPackages.cuda_nvcc # added by Jacek - cuda toolkit/compiler
     gcc-unwrapped
     python314
     superTux
     superTuxKart
     extremetuxracer
     freshfetch 
     conky #nvidia overlay for displaying temps etc.
     nvtopPackages.nvidia #enables nvtop terminal app which displays gpu usage
  ];

  # List services that you want to enable:
	
  #added by Jacek - for gaming:
  hardware.graphics.enable = true;
  services.xserver.videoDrivers = ["nvidia"];
  hardware.nvidia = {
      modesetting.enable = true;
      # Nvidia power management. Experimental, but can fix suspend/resume issues.
      powerManagement.enable = false; 
      # Fine-grained power management. Turns off GPU when not in use.
      # Experimental and only works on modern Nvidia GPUs (Turing or newer).
      powerManagement.finegrained = false;

      # Use the NVidia open source kernel module (not to be confused with Nouveau)
      # Try setting this to "false" if "true" is causing issues. 
      # "true" is recommended for RTX 2000 series and newer.
      open = false;

      # Enable the Nvidia settings menu,
      # accessible via `nvidia-settings`.
      nvidiaSettings = true;

      # Selecting the specific package is often safer than 'stable'
      # package = config.boot.kernelPackages.nvidiaPackages.stable; 
      # Or typically:
      package = config.boot.kernelPackages.nvidiaPackages.production;
      #package = config.boot.kernelPackages.nvidiaPackages.stable;
      
   };

   programs.steam.enable = true;
   programs.steam.gamescopeSession.enable = true;
   programs.gamemode.enable = true;
   #added by JAcek to control sys fan by gpu temps. You must set "full speed" for the desired fans in the BIOS; Otherwise BIOS 'fan control' will override whatever you select in Liunx.
   programs.coolercontrol = {
       enable = true;
       nvidiaSupport = true;
   };
  

   environment.sessionVariables = {
	STEAM_EXTRA_COMPAT_TOOLS_PATHS = "/home/user/.steam/root/compatibilitytools.d";# this path is required to run protonup in cmd...
   };
 
  # Enable the OpenSSH daemon.
  # services.openssh.enable = true;

  # Open ports in the firewall.
  # networking.firewall.allowedTCPPorts = [ ... ];
  # networking.firewall.allowedUDPPorts = [ ... ];
  # Or disable the firewall altogether.
  # networking.firewall.enable = false;

  # This value determines the NixOS release from which the default
  # settings for stateful data, like file locations and database versions
  # on your system were taken. It‘s perfectly fine and recommended to leave
  # this value at the release version of the first install of this system.
  # Before changing this value read the documentation for this option
  # (e.g. man configuration.nix or on https://nixos.org/nixos/options.html).
  system.stateVersion = "24.05"; # Did you read the comment?

}
