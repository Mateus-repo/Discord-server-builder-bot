# 📄 Guia: Como criar um ficheiro `.json` (Server Template)

Este guia explica como criar o teu próprio template `.json` para o bot **Discord Server Builder** reestruturar um servidor.

---

## 1. O que é o template?

É um ficheiro `.json` com a estrutura completa que queres que o servidor tenha:
- Uma **lista** (array) de categorias.
- Cada categoria tem um **nome** e uma **lista de canais**.
- Cada canal tem um **nome** e um **tipo**.

Quando usas `/setup-server`, o bot:
1. **Apaga** todos os canais e categorias `não protegidos`;
2. **Recria** tudo a partir do teu `.json`.

> ⚠️ O setup é destrutivo: tudo o que não estiver no template (e não estiver protegido) é apagado.

---

## 2. Estrutura básica

```json
[
  {
    "name": "Nome da Categoria",
    "channels": [
      { "name": "canal-1", "type": "text" },
      { "name": "Canal Voz", "type": "voice" }
    ]
  }
]
```

| Parte | O que é |
|---|---|
| `[ ... ]` | A raiz tem de ser sempre um array (lista de categorias) |
| `"name"` (categoria) | Nome da categoria no Discord |
| `"channels"` | Array de canais dentro da categoria |
| `"name"` (canal) | Nome do canal |
| `"type"` | Tipo do canal (ver secção 3) |

Cada objeto deve ser separado por `,` (vírgula). **Nunca** deixes uma vírgula antes do último `}` ou `]` — o JSON é inválido e o bot devolve erro.

---

## 3. Tipos de canal suportados

Definidos no `bot.py` (`TYPE_MAP`):

| `"type"` | Canal Discord | Notas |
|---|---|---|
| `"text"` | Texto | Padrão. Usado se omites o `"type"` |
| `"voice"` | Voz | |
| `"forum"` | Fórum | Baseado em conversas/threads |
| `"announcement"` | Anúncios | Também aceite como `"news"` |
| `"news"` | Anúncios | Alias de `"announcement"` |
| `"stage"` | Palco | Eventos de áudio ao vivo |

> Qualquer outro valor (ou mau escrita) cai para `text` automaticamente. Não há erro — verifica bem se queres outro tipo.

Se omites `"type"`, o canal é criado como **texto**:

```json
{ "name": "geral" }
```

é o mesmo que:

```json
{ "name": "geral", "type": "text" }
```

---

## 4. Regras para os nomes

- **Canais de texto/anúncios/fóruns** — o Discord converte espaços e letras maiúsculas em minúsculas e `-`. Ex.: `Meu Canal` → `meu-canal`.
- **Canais de voz e categorias** — podem ter espaços e caracteres especiais.
- **Emojis e caracteres Unicode** — são permitidos (os templates reais usam muito isto, ex.: `server-template.json`, `server-template-vyea.json`).
- **Nomes de canais dentro da categoria** — `discord.utils.get` compara pelo nome real, por isso usa sempre exatamente o nome que queres ver no final.

Exemplo com emojis (como os ficheiros reais do projeto):

```json
  {
    "name": "🎮 Categoria: Jogos",
    "channels": [
      { "name": "para-jogar-juntos", "type": "text" },
      { "name": "sugestoes-watchlist", "type": "forum" }
    ]
  }
```

---

## 5. Caso especial: `📂 Sem Categoria` (canais soltos)

O bot também aceita uma categoria chamada `📂 Sem Categoria`. É usada pelo `/export-structure` para canais que não estão dentro de nenhuma categoria, e o bot trata-os como **canais soltos** (sem categoria):

```json
  {
    "name": "📂 Sem Categoria",
    "channels": [
      { "name": "Cooms: CLOSED!!!", "type": "voice" }
    ]
  }
```

Ver `server-template.json` (último item) ou o código em `bot.py:389`.

---

## 6. Canais protegidos (`/protect`)

Canais marcados como **protegidos** (via `/protect`) **não são apagados** durante o setup:

- O canal permanece na categoria dele (mesmo que a categoria seja recriada pelo template);
- Os restantes canais da categoria são apagados e recriados;
- Se um canal protegido estiver listado no template, é **ignorado** (`SKIPPED #... (protected)`).

Isto é útil para fóruns com posts importantes, canais de logs, etc.

Os IDs protegidos ficam em `protected-channels.json`.

---

## 7. Exemplos completos

### Mínimo — uma categoria com 2 canais

```json
[
  {
    "name": "Geral",
    "channels": [
      { "name": "chat", "type": "text" },
      { "name": "Voz Geral", "type": "voice" }
    ]
  }
]
```

### Várias categorias com tipos diferentes

```json
[
  {
    "name": "Info",
    "channels": [
      { "name": "regras", "type": "text" },
      { "name": "anuncios", "type": "announcement" }
    ]
  },
  {
    "name": "Comunidade",
    "channels": [
      { "name": "geral", "type": "text" },
      { "name": "ideias", "type": "forum" },
      { "name": "Evento Voz", "type": "stage" }
    ]
  }
]
```

> Para referência, esta é a **estrutura real** de um dos templates do projeto (`server-template-vyea.json`):

```json
[
  {
    "name": "❛⸺ who goes there 𓈒",
    "channels": [
      { "name": "rules𝄈﹒", "type": "text" },
      { "name": "welc𝄈﹒", "type": "text" },
      { "name": "sayonara𝄈﹒ᯇ★", "type": "text" }
    ]
  },
  {
    "name": "❛⸺ community 𓈒",
    "channels": [
      { "name": "𝄈﹒general", "type": "text" },
      { "name": "𝄈﹒suggestions", "type": "forum" },
      { "name": "𝄈﹒media", "type": "text" }
    ]
  }
]
```

---

## 8. Como usar o template

### Opção A — Enviar o ficheiro (recomendado)

Em Discord: `/setup-server` e anexar o ficheiro `.json` no campo **file**.

### Opção B — Colar o texto

Em Discord: `/setup-server` e colar o JSON no campo **plan**.

### Opção C — Ficheiro local

Edita o `server-template.json` (ou cria outro ficheiro `.json`) e envia-o como anexo.

---

## 9. Erros comuns e validação

| Problema | Resultado |
|---|---|
| Raiz não é um array (`{}` em vez de `[]`) | Erro de JSON/inválido |
| Vírgula a mais `[ "a", ]` | Erro de JSON |
| Aspas em falta ou erradas | Erro de JSON |
| Marca de acentuação/acento em texto normal | `\u00e9` num template exportado — normal, funciona na mesma |
| Tipo inválido (ex.: `"texto"`) | Canal criado como `text` (sem erro) |
| `cd = True`/mudar de caminho no ficheiro | Não é suportado pelo template — o bot cria sempre tudo dentro de categorias |

**Dica:** valida o teu `.json` num validador online (ex.: `jsonlint.com`) antes de usar, para evitares erros do Discord com o `/setup-server`.

> Se o teu servidor tiver o `/export-structure`, ele gera automaticamente um `server-template.json` e um `estrutura.md` da estrutura atual — podes usar isso como ponto de partida e editar.

---

## 10. Ficheiros de referência no projeto

| Ficheiro | Descrição |
|---|---|
| `server-template.json` | Template real (privado, gitignored) — canais com emojis/Unicode |
| `server-template.example.json` | Exemplo público e limpo |
| `server-template-vyea.json` | Exemplo com estética Unicode |
| `server-template-parlor.json` | Exemplo com estética Unicode |
| `bot.py` | Código que lê o JSON (`parse_plan`, `TYPE_MAP`) |