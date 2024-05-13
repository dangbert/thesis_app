#!/bin/bash
# this script installs dependencies for on the server
set -e

ENV="" # "yum" | "apt"

function main() {
  while getopts "hi" arg; do
    case $arg in
      h | --help)
        usage
        exit 0
        ;;
      i)
        generic_installs
        init_site
        echo -e "\ninitalization complete!"
        exit 0
        ;;
    esac
  done

  generic_installs

  echo -e "\nsetup.sh complete!"
  exit 0

}

function usage() {
  echo -e "Script for installing dependencies on server."
    echo -e "\nUSAGE:"
    echo -e "\tsetup.sh [-i] [-h]\n"
    echo -e "\tsetup.sh       # install most dependencies"
    echo -e "\tsetup.sh -i    # ininitalize SSL certs, and clone codebase"
    echo -e "\tsetup.sh -h    # show this help and exit"
}

function generic_installs() {
  if [[ `command -v yum` ]]; then
    ENV="yum"
    echo "seting up in debian environment"
    setup_yum
  elif [[ `command -v apt` ]]; then
    ENV="apt"
    echo "seting up in ubuntu environment"
    setup_apt
  else
    echo "unsure which environment to setup!"
    exit 1
  fi
}

# setup site in debian environment
function setup_yum {
  ensure_ssh_keys
  sudo yum update -y

  sudo yum install -y docker git tree rsync ncdu tmux
  sudo systemctl enable docker && sudo systemctl start docker
  sudo amazon-linux-extras install -y epel # needed to install certbot

  # docker compose doesn't work as a command on amazon linux :(
  if [[ ! `command -v docker-compose` ]]; then
    # https://gist.github.com/npearce/6f3c7826c7499587f00957fee62f8ee9
    sudo curl -L https://github.com/docker/compose/releases/download/1.22.0/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    # enable running docker without sudo
    sudo usermod -aG docker $USER
    echo "rebooting is likely required to run docker without sudo"
  else
    echo "docker-compose already installed ✅"
  fi
}

# setup site in ubuntu environment
function setup_apt {
  ensure_ssh_keys
  sudo apt update
  sudo apt install -y git rsync ncdu tmux
  ensure_docker_apt
}


function ensure_docker_apt {
  if [[ ! `command -v docker` ]]; then
    # https://docs.docker.com/engine/install/ubuntu/
    sudo apt install -y ca-certificates curl gnupg lsb-release
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin #docker-compose

    sudo usermod -aG docker $USER
    echo "rebooting is likely required to run docker without sudo"
    sudo systemctl enable docker && sudo systemctl start docker
  else
     echo "docker already installed ✅"
  fi
}

function ensure_ssh_keys {
 if [ `ls ~/.ssh/id* 2>/dev/null | wc -l` -eq 0 ]; then
   echo "creating ssh keys"
   ssh-keygen -t ed25519 -C "$USER@$HOSTNAME" -f ~/.ssh/id_ed25519 -N ""
   echo -e "\npublic key is:"
   cat ~/.ssh/id_ed25519.pub
   echo "visit https://github.com/settings/ssh/new to add to github"
 else
   echo "ssh key already exists ✅"
 fi
}

function init_site {
  if [[ ! `command -v certbot` ]]; then
    sudo "$ENV" install -y certbot
    echo -e "\nchoose 'Spin up temporary webserver' for authenticating in the next step.\n"
    sudo certbot certonly
  fi

  INSTALL_DIR="$HOME/thesis_app"
  if [[ ! -d "$INSTALL_DIR" ]]; then
    git clone git@github.com:dangbert/thesis_app.git "$INSTALL_DIR"
  else
     echo "site already setup ✅"
  fi
}

main "$@"
