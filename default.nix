{ pkgs ? import <nixpkgs> {} }:
let
  pythonPackages = pkgs.python3Packages;
  # Function to create a Python package with a specific version
  pythonPackageWithVersion = pname: version: attrs:
    pythonPackages.buildPythonPackage {
      inherit pname version;
      src = pkgs.fetchPypi {
        inherit pname version;
        inherit (attrs) sha256;
      };
      propagatedBuildInputs = attrs.propagatedBuildInputs or [];
    };
  # Explicitly define proglog with a specific version
  proglog = pythonPackageWithVersion "proglog" "0.1.10" {
    sha256 = "sha256-ZYwoycguTK6y8l9Ij/+c6s4i+NabFdDByG1kJ15N2rQ=";
  };
  # MoviePy dependencies
  moviepyDeps = [
    pythonPackages.decorator
    pythonPackages.imageio
    pythonPackages.imageio-ffmpeg
    pythonPackages.tqdm
    pythonPackages.numpy
    pythonPackages.requests
    proglog  # Use the explicitly defined proglog
  ];
  # Optional dependencies
  optionalDeps = [
    pythonPackages.opencv4
    pythonPackages.scikitimage
    pythonPackages.scikitlearn
    pythonPackages.scipy
    pythonPackages.matplotlib
    pkgs.yt-dlp
  ];
  # Create a custom MoviePy package from local source
  customMoviePy = pythonPackages.buildPythonPackage {
    pname = "moviepy";
    version = "1.0.3";  # Update this to match the version you're using
    format = "setuptools";
    src = ~/CustomRepos/moviepy;  # Path to your local MoviePy repository
    nativeBuildInputs = [ 
      pythonPackages.setuptools 
      pythonPackages.wheel
    ];
    propagatedBuildInputs = moviepyDeps ++ optionalDeps;
  };
  # Custom Python environment with MoviePy and its dependencies
  customPython = pkgs.python3.withPackages (ps: [ customMoviePy ] ++ moviepyDeps ++ optionalDeps);
in pkgs.mkShell {
  buildInputs = [
    customPython
    pkgs.ffmpeg
    pkgs.zsh
    pkgs.yt-dlp
  ];
  shellHook = ''
    echo "Welcome to the ClipGenerator project environment"
    echo "Python environment activated with custom MoviePy and required packages for video processing"
    echo "FFmpeg and yt-dlp are available (installed globally)"
    echo "ZSH is available for use"
    
    export PROJECT_ROOT=$(pwd)
    export TEMPLATES_FILE="$PROJECT_ROOT/templates.json"
    export UNEDITED_DIR="$PROJECT_ROOT/Uneditied"
    export EDITED_DIR="$PROJECT_ROOT/Edited"
    
    echo "Project structure:"
    echo "  - Main script: $PROJECT_ROOT/main.py"
    echo "  - Templates: $TEMPLATES_FILE"
    echo "  - Unedited videos: $UNEDITED_DIR"
    echo "  - Edited output: $EDITED_DIR"
    
    # Start zsh
    exec zsh
  '';
}
