import {
    iniciarFilas,
    salvarMensagemRecebida,
    listarMensagensSaida,
    lerMensagem,
    removerMensagem,
} from "./fila.js";

import {
    conectar,
    enviarMensagem
} from "./whatsapp.js";

let processandoFila = false;

/*
|--------------------------------------------------------------------------
| Processa mensagens da fila de saída
|--------------------------------------------------------------------------
*/

async function processarFila() {

    if (processandoFila)
        return;

    processandoFila = true;

    try {

        const arquivos = listarMensagensSaida();

        for (const arquivo of arquivos) {

    let dados;

    try {

        dados = lerMensagem(arquivo);

    }
    catch (erro) {

        console.log(`Arquivo ${arquivo} ainda não está pronto.`);
        continue;

    }

    if (!dados.numero || !dados.mensagem) {
        removerMensagem(arquivo);
        continue;
    }

    console.log("----------------------------------");
    console.log("Enviando mensagem");
    console.log("Número :", dados.numero);
    console.log("Texto  :", dados.mensagem);

        await enviarMensagem(
            dados.numero,
            dados.mensagem
        );

        removerMensagem(arquivo);

        console.log("Mensagem enviada.\n");

    }

    }
    catch (erro) {

        console.log("Erro ao enviar:");
        console.log(erro.message);

    }
    finally {

        processandoFila = false;

    }

}

/*
|--------------------------------------------------------------------------
| Inicialização
|--------------------------------------------------------------------------
*/

async function main() {

    iniciarFilas();

    await conectar((mensagem) => {

        console.log("----------------------------------");
        console.log("Nova mensagem recebida");
        console.log(mensagem);

        salvarMensagemRecebida(mensagem);

    });

    // Processa arquivos que já existirem
    await processarFila();

    // Verifica a fila continuamente
    setInterval(() => {

        processarFila();

    }, 500);

}

main().catch(console.error);