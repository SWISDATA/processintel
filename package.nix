{
  lib,
  python3,
  nix-gitignore,
  ...
}:
let
  my-python = python3.override {
    packageOverrides = self: super: {
      ddcal = self.buildPythonPackage rec {
        pname = "ddcal";
        version = "1.2.0";
        pyproject = true;

        src = self.fetchPypi {
          inherit pname version;
          hash = "sha256-sWPU98twsgbKb6i1iIQZQGAN42I3OrkEcBgKGXoRj9Q=";
        };

        postPatch = ''
          substituteInPlace pyproject.toml \
            --replace 'license = "MIT"' 'license = { text = "MIT" }'
          # Delete existing license-files line if present
          sed -i '/license-files/d' pyproject.toml
          # Append new section cleanly
          echo >> pyproject.toml
          echo '[tool.setuptools]' >> pyproject.toml
          echo 'license-files = ["LICEN[CS]E*"]' >> pyproject.toml
        '';

        doCheck = false;

        build-system = [
          self.setuptools
          self.wheel
        ];

      };
    };
  };
in
my-python.pkgs.buildPythonApplication rec {
  pname = "processintel";
  version = "v1";
  format = "pyproject";

  src = nix-gitignore.gitignoreSource [ ] (lib.cleanSource ./.);

  propagatedBuildInputs = with my-python.pkgs; [
    numpy
    pandas
    graphviz
    ddcal
    streamlit
    uvicorn
  ];

  nativeBuildInputs = with my-python.pkgs; [
    setuptools
    wheel
  ];

  nativeCheckInputs = with my-python.pkgs; [
    parameterized
    black
  ];

  checkPhase = ''
    echo "Run Unittests"
    python -m unittest discover -s tests -p "*_test.py" -v

  '';

  postInstall = ''
    mkdir -p $out/docs/algorithms
    mkdir -p $out/assets

    cp -r $src/docs/algorithms/* $out/docs/algorithms
    cp -r $src/assets/* $out/assets
  '';

}
