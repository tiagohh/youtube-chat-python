# YouTube Chat Python — Documentação em Português (BR)

Este projeto é um aplicativo Python que conecta ao chat ao vivo do YouTube e gerencia sessões de chat, salvando os dados em arquivos XLSX. Ele fornece funcionalidades para autenticar com a API do YouTube, recuperar mensagens do chat e lidar com eventos.

**EM DESENVOLVIMENTO — mas já funciona! 🚀**

---

## Docker — Firefox remoto + registro automático do chat

Execute o Firefox dentro de um container Docker e controle-o de qualquer navegador ou celular Android via noVNC. O scraper de chat roda automaticamente como dono do canal — capturando todas as mensagens, ações de moderação, banimentos, timeouts e mensagens deletadas — e salva tudo em um arquivo **XLSX**.

### Formato do arquivo XLSX

O arquivo é salvo em `./Logs/chat-AAAA-MM-DD_HH-MM-SS.xlsx` na sua máquina e contém **três abas**:

| Aba | Conteúdo |
|---|---|
| `Chat` | Todas as mensagens e eventos de moderação |
| `VDS` | Apenas usuários banidos (espelhado do Chat) |
| `Livestream URL` | URL da live capturada na inicialização |

Todas as abas compartilham **cinco colunas** (cabeçalho com fundo azul claro, negrito, maiúsculas):

| TIME | USER | MESSAGE | STATUS | MOD ACTION |
|---|---|---|---|---|
| 2026-02-25 10:30:01 | StreamFan99 | Olá pessoal! | | |
| 2026-02-25 10:31:10 | BadActor | mensagem errada | `Deleted by user` | |
| 2026-02-25 10:32:00 | TrollUser | [ofensivo] | `Deleted by mod` | ModSarah |
| 2026-02-25 10:32:30 | SpamBot | Compre seguidores! | `Hidden` | |
| 2026-02-25 10:33:00 | TrollUser | outro comentário | `Timeout – 10 min` | ModJohn |
| 2026-02-25 10:34:00 | BannedUser | última mensagem | `Banned` | ModSarah |

**Valores de STATUS:** em branco · `Deleted by user` · `Deleted by mod` · `Hidden` · `Timeout – X min` · `Banned`

Ações de moderação com atraso (ex: mensagem deletada 30 s após ser enviada) atualizam a linha original — sempre uma linha por mensagem.

### Serviços iniciados pelo `docker compose up`

| Serviço | Função | Porta |
|---|---|---|
| `youtube-chat` | Firefox + área de trabalho remota via noVNC + scraper | 6080 |
| `portainer` | Interface web para gerenciar Docker (iniciar/parar do celular) | 9443 |
| `cloudflared` | Túnel seguro — acesso de fora de casa | configurado no `.env` |

### Pré-requisitos

* [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/) instalados na máquina que vai rodar os containers (seu servidor ou PC em casa).
* Uma conta gratuita no [Cloudflare](https://dash.cloudflare.com) para o túnel (opcional — remova o serviço `cloudflared` se só precisar de acesso pela rede local).

### Configuração inicial (apenas uma vez)

```bash
# 1. Clone o repositório
git clone https://github.com/tiagohh/youtube-chat-python.git
cd youtube-chat-python

# 2. Crie seu arquivo .env
cp .env.example .env
# Edite o .env e preencha:
#   YOUTUBE_CHANNEL_URL  — URL do seu canal, ex: https://www.youtube.com/@SeuCanal
#   VNC_PASSWORD         — uma senha forte para o desktop remoto
#   CLOUDFLARE_TUNNEL_TOKEN — obtido em dash.cloudflare.com → Zero Trust → Tunnels

# 3. Inicie tudo
docker compose up --build

# 4. Abra o desktop remoto no seu navegador
#    http://localhost:6080/vnc.html   (rede local)
#    https://seu-tunel.trycloudflare.com  (acesso remoto — veja o painel do Cloudflare)

# 5. Faça login no Google como dono do canal (apenas uma vez)
#    O Firefox salva o login em ./firefox-profile — sobrevive a reinicializações do container.
```

### Toda vez depois da configuração inicial

```bash
docker compose up
```

O Firefox abre já logado, navega para `YOUTUBE_CHANNEL_URL/live` e começa a registrar automaticamente. O arquivo XLSX aparece em `./Logs/`.

### Gerenciamento remoto pelo Android

1. Abra `https://localhost:9443` (ou a URL do túnel Cloudflare) no navegador do Android.
2. Faça login no Portainer (defina sua senha de admin na primeira visita).
3. Toque em **Start** no container `youtube-chat` para iniciar uma sessão.
4. Abra a URL do noVNC para ver o Firefox em tempo real.

### Variáveis de ambiente (arquivo `.env`)

| Variável | Padrão | Descrição |
|---|---|---|
| `YOUTUBE_CHANNEL_URL` | `https://www.youtube.com/@SeuCanal` | URL do canal; o scraper adiciona `/live` para encontrar a live ativa |
| `VNC_PASSWORD` | `changeme` | Senha para o desktop remoto via noVNC |
| `CLOUDFLARE_TUNNEL_TOKEN` | — | Token do túnel obtido no painel do Cloudflare |
| `POLL_INTERVAL` | `2` | Segundos entre leituras do DOM |
| `RETRY_INTERVAL` | `60` | Segundos de espera antes de tentar novamente se não houver live |

### Segurança

* A senha VNC é definida no `.env` — use um valor forte e único.
* O perfil do Firefox (`./firefox-profile/`) contém seus cookies de login do Google. Está excluído do Git pelo `.gitignore` — **nunca faça commit dele**.
* O Portainer monta o socket do Docker (`/var/run/docker.sock`). Mantenha o Portainer atrás do túnel Cloudflare (não exposto diretamente à internet) e defina uma senha de admin forte.
* O Cloudflare Tunnel cuida da criptografia HTTPS — não é necessário abrir portas no roteador.

---

## Userscript Tampermonkey (sem Docker)

Se você já tem Firefox (ou qualquer navegador baseado em Chromium) no seu dispositivo, pode instalar o userscript diretamente.

1. Instale o [Tampermonkey](https://www.tampermonkey.net/) no seu navegador.
2. Abra `tampermonkey/youtube_chat_logger.user.js` deste repositório e clique em **Instalar** quando o Tampermonkey perguntar.
3. Acesse qualquer live do YouTube — um painel **🔴 Chat Logger** aparecerá no canto inferior direito.
4. Clique em **⬇ Download XLSX** a qualquer momento para salvar o registro.

O script captura as mesmas cinco colunas (`TIME`, `USER`, `MESSAGE`, `STATUS`, `MOD ACTION`) em três abas (`Chat`, `VDS`, `Livestream URL`). Ações de moderação com atraso atualizam a linha original.

> **Nota:** O XLSX gerado pelo script no navegador não terá os cabeçalhos estilizados com fundo azul (limitação das bibliotecas XLSX para browser). A versão Docker/Python gera o arquivo completamente estilizado.

---

## Estrutura do Projeto

```
youtube-chat-python
├── src
│   ├── youtube_chat.py          # Script principal (versão API)
│   ├── docker_scraper.py        # Scraper Docker com XLSX
│   ├── client
│   │   └── youtube_client.py    # Conexão com a API do YouTube
│   ├── handlers
│   │   └── chat_handler.py      # Processa mensagens do chat
│   └── ui
│       └── chat_ui.py           # Interface gráfica (tkinter)
├── tampermonkey
│   └── youtube_chat_logger.user.js  # Userscript para o navegador
├── Dockerfile                   # Imagem Docker
├── docker-compose.yml           # 3 serviços: youtube-chat, portainer, cloudflared
├── entrypoint.sh                # Inicialização do container
├── requirements.txt             # Dependências (versão API)
├── requirements-docker.txt      # Dependências Docker (selenium, openpyxl)
├── .env.example                 # Exemplo de variáveis de ambiente
└── README-PTBR.md               # Esta documentação
```

---

## Uso (versão API Python original)

O projeto inclui uma interface gráfica simples e registro de mensagens via API do YouTube.

### Executando
```
python src/youtube_chat.py
```

Uma janela chamada **YouTube Chat** irá aparecer. Digite ou confirme as credenciais quando solicitado e clique em **Connect**.

> 💡 Para rodar sem interface (ex: logging automatizado), instancie `ChatHandler` sem objeto `ui` e chame `chat.start_chat_session()`.

---

## Contribuindo

Sinta-se à vontade para enviar issues ou pull requests para melhorias ou correções.

## Licença

Este projeto está sob a licença MIT.




Este projeto é um aplicativo Python que conecta ao chat ao vivo do YouTube e gerencia sessões de chat, salvando em arquivos CSV. Ele fornece funcionalidades para autenticar com a API do YouTube, recuperar mensagens do chat e lidar com eventos.

**EM DESENVOLVIMENTO, TIPO EM DESENVOLVIMENTO, NÃO SEI O QUE ESTOU FAZENDO COM MINHA VIDA**

## Estrutura do Projeto

```
youtube-chat-python
├── src
│   ├── youtube_chat.py          # Script principal para gerenciar o chat do YouTube
│   ├── client
│   │   ├── __init__.py          # Inicialização do pacote client
│   │   └── youtube_client.py    # Gerencia a conexão com a API do YouTube
│   ├── handlers
│   │   └── chat_handler.py      # Processa mensagens recebidas do chat
│   └── utils
│       └── auth.py              # Funções utilitárias para autenticação
├── tests
│   └── test_chat.py             # Testes unitários para o chat
├── requirements.txt             # Dependências do projeto
├── .env.example                 # Exemplo de variáveis de ambiente
├── .gitignore                   # Arquivos ignorados pelo Git
└── README.md                    # Documentação do projeto
```

## Instruções de Instalação

1. Clone o repositório:
   ```
   git clone <repository-url>
   cd youtube-chat-python
   ```

2. Crie um ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows use `venv\Scripts\activate`
   ```

3. Instale as dependências necessárias:
   ```
   pip install -r requirements.txt
   ```

4. Configure suas variáveis de ambiente:
   - Copie `.env.example` para `.env` e preencha com suas chaves e segredos da API.

## Uso

O projeto agora inclui uma interface gráfica simples e registro de mensagens.

### Prompt de Credenciais
Se não quiser exportar variáveis de ambiente ou hardcodear, basta rodar o script e uma pequena janela irá pedir:

* **API key**
* **Video ID** (ID do vídeo do YouTube com chat ao vivo)

### Opções de Armazenamento

### Estrutura das pastas de saída

Por padrão, todos os outputs são organizados na pasta `Logs/` com subpastas para cada tipo:

* `Logs/TXT/` — arquivos de log (ex: `chat [YYYYMMDD_HHMMSS].log`)
* `Logs/Chat Principal CSV/` — arquivos CSV (ex: `chat [YYYYMMDD_HHMMSS].csv` ou `chat.csv` para execuções não versionadas)
* `Logs/ChatDatabase/` — arquivos SQLite (ex: `chat [YYYYMMDD_HHMMSS].db`)

Cada execução cria um novo arquivo com timestamp para log, CSV e banco de dados. O nome do CSV pode ser sobrescrito pela variável de ambiente `CHAT_CSV_FILE`.

Você pode desabilitar o banco de dados ou mudar o caminho editando a instância de `ChatHandler` em `src/youtube_chat.py`. O helper embutido já seleciona caminhos padrão, então normalmente não precisa mudar nada, a menos que queira outro local.

### Executando
```
python src/youtube_chat.py
```

Uma janela chamada **YouTube Chat** irá aparecer; digite ou confirme as credenciais quando solicitado e clique em **Connect**. As mensagens irão aparecer na janela e estarão disponíveis depois em `chat.log` ou no banco SQLite.

Você ainda pode pré-definir as variáveis de ambiente ou usar um arquivo `.env` se preferir; a interface só irá pedir quando valores estiverem ausentes.

> 💡 Para rodar sem interface (ex: logging automatizado), basta instanciar `ChatHandler` sem objeto `ui` e chamar `chat.start_chat_session()` no seu próprio script.

## Contribuindo

Sinta-se à vontade para enviar issues ou pull requests para melhorias ou correções.

## Licença

Este projeto está sob a licença MIT.

## Exemplos de Uso de Cota

### Exemplo 1: Stream de 1 Hora (Estimativa)

Se você transmitir por 1 hora com um intervalo de polling de 18 segundos:

- **Segundos em 1 hora:** 3.600
- **Intervalo de polling:** 18 segundos
- **Requisições por hora:** 3.600 ÷ 18 = 200 requisições
- **Unidades de cota usadas:** 200 requisições × 5 unidades = **1.000 unidades**

**Resultado:**  
Uma stream de 1 hora com intervalos de 18 segundos usará cerca de **1.000 unidades** da sua cota diária de 10.000 unidades.

---

### Exemplo 2: Stream de 10 Horas (Estimativa)

Se você transmitir por 10 horas com um intervalo de polling de 18 segundos:

- **Segundos em 10 horas:** 36.000
- **Intervalo de polling:** 18 segundos
- **Requisições em 10 horas:** 36.000 ÷ 18 = 2.000 requisições
- **Unidades de cota usadas:** 2.000 requisições × 5 unidades = **10.000 unidades**

**Resultado:**  
Uma stream de 10 horas com intervalos de 18 segundos usará toda a sua cota diária de **10.000 unidades**.

---

**Nota:**  
Ajuste o intervalo de polling de acordo com suas horas planejadas de transmissão para não exceder sua cota diária. A cota é reiniciada a cada 24 horas. Se o chat estiver muito ativo, intervalos maiores podem resultar em algumas mensagens não sendo capturadas.

---

## Como Alterar o Intervalo de Polling (Guia Absurdo)

Para ajustar o intervalo de polling no coletor de chat do YouTube:

### Passo 1: Encontre o Intervalo

Abra o arquivo:
```
src/youtube_chat.py
```
Dentro da classe `YouTubeChat`, no método `start_chat_session`, procure:
```python
time.sleep(18)  # Polling interval
```
Troque o número para o intervalo desejado em segundos:
```python
time.sleep(10)  # Polling interval
```
Salve e reinicie o app.

Lembre-se:
- Intervalo menor captura mais mensagens, mas consome mais cota.
- Intervalo maior economiza cota, mas pode perder mensagens em chats movimentados.

---

## TDC

A configuração do chat ao vivo do YouTube pode causar problemas. Se o chat estiver como "apenas para membros", "apenas para inscritos" ou restrito por idade, região ou moderação, a API pode não retornar o ID do chat ao vivo ou mensagens, mesmo com a transmissão ativa. Se for estreia ou replay, o chat ao vivo pode não estar acessível pela API.

Verifique:
- O chat é público e não restrito a membros/inscritos.
- A transmissão está realmente ao vivo (não replay ou agendada).
- Não há restrições de idade ou região.
- A chave da API tem acesso aos escopos necessários da API de Dados do YouTube.
- Não há restrições de idade ou região.

- A chave da API tem acesso aos escopos necessários da API de Dados do YouTube.
