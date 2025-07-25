# To learn more about how to use Nix to configure your environment
# see: https://developers.google.com/idx/guides/customize-idx-env
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"
  # Use https://search.nixos.org/packages to find packages
  packages = [
    # Python 3.11 for better CrewAI compatibility (avoid 3.13 issues)
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel
    # Build tools that CrewAI dependencies might need
    pkgs.gcc
    pkgs.pkg-config
    # Optional: Add other tools you might need
    # pkgs.nodejs_20
    # pkgs.nodePackages.nodemon
  ];
  
  # Sets environment variables in the workspace
  env = {
    # Ensure pip uses the virtual environment
    VIRTUAL_ENV = ".venv";
    # Set Python path
    PYTHONPATH = ".venv/lib/python3.11/site-packages:$PYTHONPATH";
  };
  
  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      # Python extensions
      "ms-python.python"
      "ms-python.vscode-pylance"
      # Optional: Add other useful extensions
      # "vscodevim.vim"
    ];
    
    # Enable previews
    previews = {
      enable = true;
      previews = {
        # You can add web previews here if needed for CrewAI web interfaces
        # web = {
        #   command = ["python" "app.py"];
        #   manager = "web";
        #   env = {
        #     PORT = "$PORT";
        #   };
        # };
      };
    };
    
    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        # Create virtual environment and install CrewAI
        create-venv = "python3.11 -m venv .venv";
        activate-and-install = "source .venv/bin/activate && pip install --upgrade pip setuptools wheel";
        install-crewai = "source .venv/bin/activate && pip install 'crewai[tools]'";
        # Open editors for the following files by default, if they exist:
        default.openFiles = [ ".idx/dev.nix" "README.md" ];
      };
      
      # Runs when the workspace is (re)started
      onStart = {
        # Activate virtual environment
        activate-venv = "source .venv/bin/activate";
        # Optional: Install any additional requirements
        # install-requirements = "source .venv/bin/activate && pip install -r requirements.txt";
      };
    };
  };
}