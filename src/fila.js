import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ENTRADA = path.join(__dirname, "..", "filas", "entrada");
const SAIDA = path.join(__dirname, "..", "filas", "saida");

/*
|--------------------------------------------------------------------------
| Garante que as pastas existam
|--------------------------------------------------------------------------
*/

export function iniciarFilas() {

    if (!fs.existsSync(ENTRADA))
        fs.mkdirSync(ENTRADA, { recursive: true });

    if (!fs.existsSync(SAIDA))
        fs.mkdirSync(SAIDA, { recursive: true });

}


/*
|--------------------------------------------------------------------------
| Salva mensagem recebida pelo WhatsApp
|--------------------------------------------------------------------------
*/

export function salvarMensagemRecebida(dados) {

    // Um arquivo por número
    const arquivo = path.join(
        ENTRADA,
        `${dados.numero}.json`
    );

    let conversa;

    // Se já existir, abre a conversa
    if (fs.existsSync(arquivo)) {

        conversa = JSON.parse(
            fs.readFileSync(arquivo, "utf8")
        );

    } else {

        // Se não existir, cria uma nova
        conversa = {
            numero: dados.numero,
            nome: dados.nome,
            mensagens: []
        };

    }

    // Atualiza o nome (caso tenha mudado)
    conversa.nome = dados.nome;

    // Adiciona a nova mensagem
    conversa.mensagens.push({
    direcao: "recebida",
    tipo: dados.tipo,
    texto: dados.mensagem,
    timestamp: dados.timestamp
});

    // Salva novamente
    fs.writeFileSync(
        arquivo,
        JSON.stringify(conversa, null, 4),
        "utf8"
    );

}

/*
|--------------------------------------------------------------------------
| Lista mensagens aguardando envio
|--------------------------------------------------------------------------
*/

export function listarMensagensSaida() {

    return fs.readdirSync(SAIDA)
        .filter(a => a.endsWith(".json"))
        .sort();

}

/*
|--------------------------------------------------------------------------
| Lê uma mensagem da fila
|--------------------------------------------------------------------------
*/

export function lerMensagem(nomeArquivo) {

    const caminho = path.join(SAIDA, nomeArquivo);

    return JSON.parse(
        fs.readFileSync(caminho, "utf8")
    );

}

/*
|--------------------------------------------------------------------------
| Remove mensagem enviada
|--------------------------------------------------------------------------
*/

export function removerMensagem(nomeArquivo) {

    const caminho = path.join(SAIDA, nomeArquivo);

    if (fs.existsSync(caminho))
        fs.unlinkSync(caminho);

}


