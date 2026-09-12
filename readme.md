# AgenteZAP

Bot que monitora mensagens do WhatsApp, identifica ofertas de produtos cadastrados e envia automaticamente um alerta quando o preço está dentro do limite definido.

## Como funciona

O projeto possui dois processos:

1. **Node.js + Baileys**
   - Conecta ao WhatsApp.
   - Recebe mensagens de grupos/canais.
   - Salva as mensagens em `filas/entrada`.
   - Envia os alertas que aparecem em `filas/saida`.

2. **Python**
   - Monitora `filas/entrada`.
   - Procura pelos produtos cadastrados.
   - Identifica o preço da oferta.
   - Compara com o preço máximo configurado.
   - Se a oferta for aprovada, cria um arquivo em `filas/saida`.

### Fluxo

WhatsApp
   ↓
Node.js
   ↓
filas/entrada
   ↓
Python
   ↓
filas/saida
   ↓
Node.js
   ↓
WhatsApp
---

# Como usar

## 1. Instale as dependências

Com o Node.js e Python instalados, abra o terminal na pasta do projeto e execute:

```bash
npm install
```

---

## 2. Configure o número de destino

Abra:

src/analisador.py

Procure:

```python
DESTINO = ""
```

Troque pelo número de WhatsApp que deverá receber os alertas.

> Use o número com código do país, sem `+`, espaços ou caracteres especiais.

**Importante:** esse é o destino dos alertas. Não precisa ser o grupo/canal de onde as ofertas são recebidas.

---

## 3. Conecte o WhatsApp

Execute:

```bash
node src/index.js
```

Na primeira execução, o sistema mostrará um **QR Code** no terminal.

Abra o WhatsApp no celular:

**Configurações → Aparelhos conectados → Conectar aparelho**

Escaneie o QR Code.

Depois da conexão, a sessão ficará salva em:

auth_info/

Nas próximas execuções, normalmente não será necessário escanear novamente.

---

## 4. Inicie o analisador

Abra **outro terminal**, na pasta do projeto, e execute:

```bash
python src/analisador.py
```

O Python ficará monitorando as mensagens recebidas.

---

# Configurando as ofertas

As ofertas são configuradas em:

src/analisador.py

Exemplo:

```python
{
    "nome": "Ryzen 5 5600",
    "aliases": [
        "ryzen 5 5600",
        "ryzen 5600"
    ],
    "preco_maximo": 650.00
}
```

Isso significa que qualquer mensagem contendo um dos aliases será considerada, desde que o preço seja de até **R$650**.

Para adicionar outro produto, basta adicionar uma nova regra.

---

# Exemplo

Se chegar no WhatsApp:

🔥 Ryzen 5 5600

💵 R$400,01

https://exemplo.com/produto

O Python identifica:

Produto: Ryzen 5 5600
Preço: R$400,01
Limite: R$650,00

Como o preço está abaixo do limite, ele cria um alerta em:

filas/saida/

O Node.js detecta o alerta e envia para o **número configurado em `DESTINO`**.

---

# Para executar

Sempre deixe os dois processos funcionando:

### Terminal 1 — WhatsApp

```bash
node src/index.js
```

### Terminal 2 — Analisador

```bash
python src/analisador.py
```

## Antes de testar, confira:

* WhatsApp conectado pelo QR Code;
* número de destino configurado em `src/analisador.py`;
* regras dos produtos configuradas;
* pastas `filas/entrada` e `filas/saida` existentes.

O sistema então funciona automaticamente enquanto os dois processos estiverem rodando.