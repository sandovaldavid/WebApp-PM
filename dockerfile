FROM python:3.12-slim-bullseye

# Evitar prompts interactivos durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Actualizar el sistema e instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    openssh-server \
    zsh \
    git \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configurar SSH
RUN mkdir /var/run/sshd && echo 'root:dev1' | chpasswd
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
RUN echo "Port 22" >> /etc/ssh/sshd_config

# Git configuration
RUN git config --global init.defaultBranch main

# Instalar Node.js (versión 20.x) directamente desde el repositorio oficial
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm

# Verificar instalación de Node.js
RUN node -v && npm -v

# Instalar GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
    dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
    tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && apt-get install -y gh

# Verificar instalación de GitHub CLI
RUN gh --version

# Instalar Oh My Zsh
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" || true

# Install nano
RUN apt-get update && apt-get install -y nano && apt-get clean && rm -rf /var/lib/apt/lists/*

# Configurar Zsh como shell predeterminado
SHELL ["/bin/zsh", "-c"]

# Instalar dependencias de Python
RUN pip install --upgrade pip
RUN pip install django djangorestframework
RUN pip install django-debug-toolbar

#Install gitmoji-cli
RUN npm i -g gitmoji-cli

# Configurar Git para evitar el error de "dubious ownership" (como el usuario creado)
RUN git config --global --add safe.directory '*'

WORKDIR /workspaces

# Establece las variables de entorno para la base de datos
ENV POSTGRES_DB=DbWebAp_PM
ENV POSTGRES_USER=development
ENV POSTGRES_PASSWORD=123456
ENV POSTGRES_HOST=db
ENV POSTGRES_PORT=5432

# Exponer el puerto predeterminado de Django
EXPOSE 8080
EXPOSE 22

# Comando por defecto
# Establecer Zsh como shell predeterminado
CMD ["/bin/zsh", "-c", "/usr/sbin/sshd -D & zsh"]