# Discord Server Builder Bot

Bot Discord que cria automaticamente categorias e canais a partir de um ficheiro Markdown.

## Como usar

### 1. Criar o bot no Discord Developer Portal

1. Vai a https://discord.com/developers/applications
2. **New Application** → dá um nome ao bot
3. Aba **Bot** → **Add Bot** → copia o **Token**
4. Aba **OAuth2 > URL Generator**:
   - Scopes: `bot`
   - Permissions: `Manage Channels`
5. Abre o link gerado para convidar o bot para o teu servidor

### 2. Configurar

```bash
# Instalar dependências
pip install -r requirements.txt

# Criar ficheiro de configuração
cp .env.example .env
```

Preenche o `.env`:

```
DISCORD_TOKEN=token_que_copiaste
GUILD_ID=id_do_teu_servidor
```

> Para obter o `GUILD_ID`: ativa o **Modo de Programador** no Discord (Definições > Avançado), clica com o botão direito no nome do servidor → **Copiar ID do Servidor**.

### 3. Executar

```bash
python bot.py
```

No Discord, usa o comando:

```
/criarservidor
```

O bot cria todas as categorias e canais definidos em `estrutura-servidor-discord.md` que ainda não existirem no servidor.

## Estrutura do projeto

```
├── bot.py                          # Bot principal
├── requirements.txt                # Dependências Python
├── .env.example                    # Template de configuração
├── .gitignore
├── estrutura-servidor-discord.md   # Estrutura do servidor (categorias e canais)
├── plano-bot-criacao-canais.md     # Plano original do projeto
└── README.md
```

## Formato do ficheiro de estrutura

O bot lê o `estrutura-servidor-discord.md` que deve seguir este formato:

```markdown
## 📋 Categoria: WishList

- `#roupas`
- `#jogos`

## 💬 Categoria: Geral

- 🔊 `Voz Geral` (canal de voz)
- `#chat`
- `#memes`
```

- `## Nome` → cria uma categoria
- `` - `#canal` `` → cria um canal de texto
- `- 🔊 Nome` → cria um canal de voz
- Linhas `>`, `---` e secção "Notas extra" são ignoradas

## Segurança

O comando `/criarservidor` só pode ser usado por administradores do servidor.
Nunca partilhes o ficheiro `.env` (contém o token do bot).

