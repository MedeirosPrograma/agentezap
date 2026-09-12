import json
import re
import time
import unicodedata
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

REGRAS = [
    # =========================
    # PLACAS-MÃE
    # =========================

    {
        "nome": "Gigabyte A520M K V2",
        "aliases": [
            "a520m k v2",
            "a520m-k v2",
            "gigabyte a520m k v2"
        ],
        "preco_maximo": 400.00
    },

    {
        "nome": "MSI B550M PRO-VDH",
        "aliases": [
            "b550m pro-vdh",
            "b550m pro vdh",
            "msi b550m pro-vdh"
        ],
        "preco_maximo": 600.00
    },


    # =========================
    # PROCESSADORES
    # =========================

    {
        "nome": "Ryzen 5 5500",
        "aliases": [
            "ryzen 5 5500",
            "ryzen 5500",
            "r5 5500"
        ],
        "preco_maximo": 500.00
    },

    {
        "nome": "Ryzen 5 5600",
        "aliases": [
            "ryzen 5 5600",
            "ryzen 5600",
            "r5 5600"
        ],
        "preco_maximo": 650.00
    },

    {
        "nome": "Ryzen 7 5700X",
        "aliases": [
            "ryzen 7 5700x",
            "ryzen 5700x",
            "r7 5700x"
        ],
        "preco_maximo": 800.00
    },

    {
        "nome": "Ryzen 7 5700X3D",
        "aliases": [
            "ryzen 7 5700x3d",
            "ryzen 5700x3d",
            "5700x3d",
            "5700 x3d"
        ],
        "preco_maximo": 1100.00
    },


    # =========================
    # MEMÓRIA RAM DDR4
    # =========================

    # 2x8 GB — só interessa se estiver realmente barata

    {
        "nome": "Kingston Fury Beast 16GB (2x8) DDR4 3200",
        "aliases": [
            "kingston fury beast 16gb",
            "fury beast 2x8 3200",
            "fury beast 16gb 3200",
            "kingston fury 2x8 3200"
        ],
        "preco_maximo": 600.00
    },

    {
        "nome": "Corsair Vengeance LPX 16GB (2x8) DDR4 3200",
        "aliases": [
            "corsair vengeance lpx 16gb",
            "vengeance lpx 2x8 3200",
            "corsair 2x8 3200",
            "corsair vengeance 16gb 3200"
        ],
        "preco_maximo": 600.00
    },


    # 2x16 GB — opção que eu priorizaria

    {
        "nome": "Kingston Fury Beast 32GB (2x16) DDR4 3200",
        "aliases": [
            "kingston fury beast 32gb",
            "fury beast 2x16 3200",
            "fury beast 32gb 3200",
            "kingston fury 2x16 3200"
        ],
        "preco_maximo": 900.00
    },

    {
        "nome": "Corsair Vengeance LPX 32GB (2x16) DDR4 3200",
        "aliases": [
            "corsair vengeance lpx 32gb",
            "vengeance lpx 2x16 3200",
            "corsair 2x16 3200",
            "corsair vengeance 32gb 3200"
        ],
        "preco_maximo": 900.00
    },


    # =========================
    # RAM AVULSA — PARA OPORTUNIDADES
    # =========================

    {
        "nome": "Kingston Fury Beast 8GB DDR4 3200",
        "aliases": [
            "kingston fury beast 8gb",
            "fury beast 8gb 3200",
            "kingston fury 8gb 3200"
        ],
        "preco_maximo": 300.00
    },

    {
        "nome": "Corsair Vengeance LPX 8GB DDR4 3200",
        "aliases": [
            "corsair vengeance lpx 8gb",
            "vengeance lpx 8gb 3200",
            "corsair 8gb 3200"
        ],
        "preco_maximo": 300.00
    }
]


# ============================================================
# CAMINHOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENTRADA = BASE_DIR / "filas" / "entrada"
SAIDA = BASE_DIR / "filas" / "saida"

if not ENTRADA.exists():
    raise FileNotFoundError(f"Pasta não encontrada: {ENTRADA}")

if not SAIDA.exists():
    raise FileNotFoundError(f"Pasta não encontrada: {SAIDA}")
INTERVALO = 0.5


# ============================================================
# CONTROLE
# ============================================================

# Guarda quantas mensagens de cada arquivo já foram analisadas.
PROCESSADOS = {}


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar(texto):

    if not texto:
        return ""

    texto = str(texto).lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = texto.encode(
        "ascii",
        "ignore"
    ).decode(
        "ascii"
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


# ============================================================
# PREÇO
# ============================================================

def converter_preco(valor):

    valor = valor.strip()

    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")

    try:
        return float(valor)
    except ValueError:
        return None


def extrair_preco(texto):

    if not texto:
        return None

    # --------------------------------------------------------
    # 1. "Por: R$ 149,90"
    # --------------------------------------------------------

    match = re.search(
        r"\bpor\b.*?"
        r"(?:R\$\s*)?"
        r"\*?"
        r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:

        preco = converter_preco(
            match.group(1)
        )

        if preco is not None:
            return preco

    # --------------------------------------------------------
    # 2. "💵 R$ 359"
    # --------------------------------------------------------

    match = re.search(
        r"💵.*?"
        r"(?:R\$\s*)?"
        r"\*?"
        r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    if match:

        preco = converter_preco(
            match.group(1)
        )

        if preco is not None:
            return preco

    # --------------------------------------------------------
    # 3. Primeiro R$
    # --------------------------------------------------------

    encontrados = re.findall(
        r"R\$\s*\*?"
        r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)",
        texto,
        flags=re.IGNORECASE
    )

    precos = []

    for valor in encontrados:

        preco = converter_preco(valor)

        if preco is not None:
            precos.append(preco)

    if precos:
        return precos[-1]

    return None


# ============================================================
# LINK
# ============================================================

def extrair_link(texto):

    if not texto:
        return None

    match = re.search(
        r"https?://[^\s]+",
        texto
    )

    if not match:
        return None

    return match.group(0).rstrip(
        ").,>\"'"
    )


# ============================================================
# PRODUTO
# ============================================================

def encontrar_produto(texto):

    texto_normalizado = normalizar(texto)

    for regra in REGRAS:

        for alias in regra["aliases"]:

            alias_normalizado = normalizar(alias)

            if alias_normalizado in texto_normalizado:

                return regra

    return None


# ============================================================
# ANALISAR OFERTA
# ============================================================

def analisar_mensagem(texto):

    produto = encontrar_produto(texto)

    if produto is None:

        return None

    preco = extrair_preco(texto)

    if preco is None:

        print(
            "[IGNORADO] Produto encontrado, mas preço não identificado."
        )

        return None

    limite = produto["preco_maximo"]

    print(
        f"[PRODUTO] {produto['nome']}"
    )

    print(
        f"[PREÇO] R$ {preco:.2f}"
    )

    print(
        f"[LIMITE] R$ {limite:.2f}"
    )

    if preco > limite:

        print(
            "[IGNORADO] Preço acima do limite."
        )

        return None

    link = extrair_link(texto)

    alerta = (
        "🚨 OFERTA ENCONTRADA!\n\n"
        f"🛒 {produto['nome']}\n"
        f"💰 R$ {preco:.2f}\n"
        f"🎯 Seu limite: R$ {limite:.2f}"
    )

    if link:

        alerta += (
            f"\n\n🔗 {link}"
        )

    print(
        "[OFERTA] PREÇO DENTRO DO LIMITE!"
    )

    return {
        "produto": produto["nome"],
        "preco": preco,
        "limite": limite,
        "link": link,
        "mensagem_alerta": alerta
    }


# ============================================================
# CRIAR ARQUIVO DE SAÍDA
# ============================================================

def criar_saida(resultado):

    # --------------------------------------------------------
    # DESTINO TEMPORÁRIO
    #
    # NUMERO AQUI
    # --------------------------------------------------------

    DESTINO = ""

    nome = (
        f"oferta_{int(time.time() * 1000)}.json"
    )

    caminho = SAIDA / nome

    dados = {
        "numero": DESTINO,
        "mensagem": resultado["mensagem_alerta"]
    }

    # Primeiro cria .tmp
    temporario = SAIDA / f"{nome}.tmp"

    with open(
        temporario,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=4
        )

    # Depois renomeia para .json
    temporario.replace(caminho)

    print()
    print("========================================")
    print("🚨 ALERTA CRIADO")
    print("========================================")
    print(f"Arquivo: {nome}")
    print(f"Destino: {DESTINO}")
    print()
    print(resultado["mensagem_alerta"])
    print("========================================")
    print()


# ============================================================
# PROCESSAR ARQUIVO
# ============================================================

def processar_arquivo(caminho):

    try:

        with open(
            caminho,
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(arquivo)

    except json.JSONDecodeError:

        # O Node ainda pode estar escrevendo o arquivo.
        return

    except OSError as erro:

        print(
            f"[ERRO] Não foi possível ler {caminho.name}: {erro}"
        )

        return

    mensagens = dados.get(
        "mensagens",
        []
    )

    if not isinstance(mensagens, list):
        return

    chave = str(caminho)

    inicio = PROCESSADOS.get(
        chave,
        0
    )

    # Só pega mensagens novas
    novas = mensagens[inicio:]

    if not novas:
        return

    print()
    print("----------------------------------------")
    print(f"📥 Arquivo: {caminho.name}")
    print(f"📨 Novas mensagens: {len(novas)}")
    print("----------------------------------------")

    for mensagem in novas:

        if not isinstance(mensagem, dict):
            continue

        if mensagem.get("direcao") != "recebida":
            continue

        texto = mensagem.get("texto")

        if not texto:
            continue

        print()
        print("Mensagem recebida:")
        print(texto)

        resultado = analisar_mensagem(
            texto
        )

        if resultado:

            criar_saida(
                resultado
            )

    # Marca todas as mensagens como processadas
    PROCESSADOS[chave] = len(mensagens)


# ============================================================
# MONITOR
# ============================================================

def monitorar():

    print()
    print("========================================")
    print("     ANALISADOR DE OFERTAS")
    print("========================================")
    print()
    print(f"Entrada: {ENTRADA}")
    print(f"Saída:   {SAIDA}")
    print()
    print("Produtos monitorados:")

    for regra in REGRAS:

        print(
            f"  - {regra['nome']} "
            f"até R$ {regra['preco_maximo']:.2f}"
        )

    print()
    print("Monitorando...")
    print()

    while True:

        try:

            arquivos = sorted(
                ENTRADA.glob("*.json")
            )

            for arquivo in arquivos:

                processar_arquivo(
                    arquivo
                )

            time.sleep(
                INTERVALO
            )

        except KeyboardInterrupt:

            print()
            print("Analisador encerrado.")
            break

        except Exception as erro:

            print(
                f"[ERRO] {type(erro).__name__}: {erro}"
            )

            time.sleep(1)


# ============================================================
# INÍCIO
# ============================================================

if __name__ == "__main__":

    monitorar()