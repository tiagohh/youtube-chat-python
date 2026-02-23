# YouTube Chat Python

OS COMENTÁRIOS DO CÓDIGO TÃO INGLÊS, TRADUZ AÍ, DÁ SEUS PULO IRMÃO, GOOGLE TRADUDOR TÁ AÍ
https://translate.google.com/?sl=en&tl=pt&op=translate



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
