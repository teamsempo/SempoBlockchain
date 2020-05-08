with import <nixpkgs> { };

let
  packages = import ./nix/ganache/default.nix { };
in
stdenv.mkDerivation {
  name = "python";
  buildInputs = [
    packages.ganache-cli

    python36
    python36Packages.pip
    python36Packages.setuptools
    python36Packages.virtualenvwrapper
    python36Packages.pandas
    python36Packages.celery

    nodejs-13_x
    redis
    redis-desktop-manager
    postgresql_12
    pgadmin
    libmysqlclient
    ncurses

    terraform_0_12
  ];
  shellHook = "
    setup() {
      virtualenv venv
    }
    install() {
      cd app
      python3 -m pip install -r slow_requirements.txt
      python3 -m pip install -r requirements.txt
      cd ../eth_worker
      python3 -m pip install -r requirements.txt
      cd ../worker
      python3 -m pip install -r requirements.txt
      cd ../test
      python3 -m pip install -r requirements.txt
    }
    export SOURCE_DATE_EPOCH=315532800
  ";
}
