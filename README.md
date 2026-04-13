# Discord Rich Presence com GUI para Linux

Interface gráfica (GTK3) para configurar e gerenciar o [linux-discord-rich-presence](https://github.com/nicholasgasior/linux-discord-rich-presence) sem precisar editar arquivos JSON ou usar o terminal.

![Plataforma](https://img.shields.io/badge/plataforma-Linux-blue)
![Python](https://img.shields.io/badge/python-3.x-blue)
![GTK](https://img.shields.io/badge/GTK-3.0-green)
![Licença](https://img.shields.io/badge/licença-MIT-lightgrey)

---

## Funcionalidades

- Configurar Application ID, details, state, imagens e botões pelo visual
- Pré-visualização em tempo real da presença
- Iniciar e parar o Rich Presence com um clique
- Mostrar tempo decorrido (elapsed)
- Suporte a Party (tamanho atual / máximo)
- Atalho no menu de aplicativos após instalação
- Configuração salva automaticamente em `~/.config/linux-discord-rich-presence/config.json`

---

## Requisitos

- Python 3
- GTK 3 bindings para Python (`python3-gi`)
- Binário `linux-discord-rich-presence` (incluído na pasta)

---

## Instalação

```bash
# 1. Baixe ou clone o repositório
git clone https://github.com/Felipe-Luvizotto/linux-discord-rich-presence-with-GUI.git
cd linux-discord-rich-presence-with-GUI

# 2. Entre na pasta e rode o instalador
cd discord-rpc-gui
chmod +x install.sh
./install.sh
```

O instalador vai:
- Verificar e instalar as dependências necessárias (GTK)
- Copiar os arquivos para `~/.local/share/discord-rpc-gui/`
- Criar o atalho `discord-rpc-gui` em `~/.local/bin/`
- Adicionar a entrada no menu de aplicativos

---

## Como usar

Após instalar, você pode abrir de duas formas:

- **Menu de aplicativos:** procure por "Discord Rich Presence"
- **Terminal:** execute `discord-rpc-gui`

### Configuração

1. Cole o **Application ID** do seu app no [Discord Developer Portal](https://discord.com/developers/applications)
2. Preencha os campos desejados (Details, State, imagens, botões, party)
3. Clique em **Salvar e Iniciar**

---

## Desinstalação

```bash
rm -rf ~/.local/share/discord-rpc-gui
rm ~/.local/bin/discord-rpc-gui
rm ~/.local/share/applications/discord-rpc-gui.desktop
```

---

## Estrutura do projeto

```
discord-rpc-gui/
├── discord-rpc-gui.py          # Interface gráfica (GTK3)
├── install.sh                  # Script de instalação
└── linux-discord-rich-presence # Binário do rich presence
```
