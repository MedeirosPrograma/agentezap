import makeWASocket, {
    useMultiFileAuthState,
    DisconnectReason
} from "@whiskeysockets/baileys";
import fs from "fs";
import qrcode from "qrcode-terminal";
import pino from "pino";

let sock = null;
/*
|--------------------------------------------------------------------------
| Configurações de leitura
|--------------------------------------------------------------------------
*/

const CONFIG = {

    lerContatos: true,

    lerGrupos: false,

    lerStatus: false,

    lerNewsletters: false,

    lerBroadcasts: false

};

function extrairMensagem(msg) {

    const m = msg.message;

    // Texto
    if (m.conversation)
        return {
            tipo: "texto",
            mensagem: m.conversation
        };

    if (m.extendedTextMessage)
        return {
            tipo: "texto",
            mensagem: m.extendedTextMessage.text
        };

    // Imagem
    if (m.imageMessage)
        return {
            tipo: "imagem",
            mensagem: m.imageMessage.caption ?? null
        };

    // Vídeo
    if (m.videoMessage)
        return {
            tipo: "video",
            mensagem: m.videoMessage.caption ?? null
        };

    // Áudio
    if (m.audioMessage)
        return {
            tipo: "audio",
            mensagem: null
        };

    // Figurinha
    if (m.stickerMessage)
        return {
            tipo: "figurinha",
            mensagem: null
        };

    // Documento
    if (m.documentMessage)
        return {
            tipo: "documento",
            mensagem: m.documentMessage.caption ?? null
        };

    // Contato
    if (m.contactMessage)
        return {
            tipo: "contato",
            mensagem: null
        };

    // Localização
    if (m.locationMessage)
        return {
            tipo: "localizacao",
            mensagem: null
        };

    // Enquete
    if (m.pollCreationMessage)
        return {
            tipo: "enquete",
            mensagem: null
        };

    // Reação
    if (m.reactionMessage)
        return {
            tipo: "reacao",
            mensagem: null
        };

    // Chamada
    if (m.call)
        return {
            tipo: "chamada",
            mensagem: null
        };

    return {
        tipo: "desconhecido",
        mensagem: null
    };

}
/*
|--------------------------------------------------------------------------
| Conecta ao WhatsApp
|--------------------------------------------------------------------------
*/

export async function conectar(onMensagem) {

    const { state, saveCreds } =
        await useMultiFileAuthState("./auth_info");

    sock = makeWASocket({
        auth: state,
        logger: pino({ level: "silent" }),
        printQRInTerminal: false,
        syncFullHistory: false,
        markOnlineOnConnect: true
    });

    sock.ev.on("creds.update", saveCreds);

    return new Promise((resolve) => {

        let conectado = false;

        sock.ev.on("connection.update", ({ connection, qr, lastDisconnect }) => {

            if (qr) {

                console.clear();

                console.log("=================================");
                console.log("ESCANEIE O QR CODE");
                console.log("=================================\n");

                qrcode.generate(qr, {
                    small: true
                });

            }

            if (connection === "open") {

                console.clear();

                console.log("=================================");
                console.log("WhatsApp conectado!");
                console.log("=================================\n");

                if (!conectado) {

                    conectado = true;

                    resolve();

                }

            }

            if (connection === "close") {

            const status =
                lastDisconnect?.error?.output?.statusCode;

            console.log("Status:", status);

            // Sessão inválida
            if (status === 401 || status === DisconnectReason.loggedOut) {

                console.log("Sessão expirada.");
                console.log("Removendo credenciais...");

                fs.rmSync("./auth_info", {
                    recursive: true,
                    force: true
                });

                console.log("Reiniciando...\n");

                setTimeout(() => {

                    conectar(onMensagem);

                }, 1000);

                return;
            }

            console.log("Conexão perdida.");

            setTimeout(() => {

                conectar(onMensagem);

            }, 3000);

        }

        });

        sock.ev.on("messages.upsert", ({ messages, type }) => {

            if (type !== "notify") return;

            for (const msg of messages) {

                if (!msg.message) continue;

                if (msg.key.fromMe) continue;

                const jid = msg.key.remoteJid;

                // Status
                if (
                    jid === "status@broadcast" &&
                    !CONFIG.lerStatus
                ) continue;

                // Grupos
                if (
                    jid?.endsWith("@g.us") &&
                    !CONFIG.lerGrupos
                ) continue;

                // Canais
                if (
                    jid?.endsWith("@newsletter") &&
                    !CONFIG.lerNewsletters
                ) continue;

                // Broadcast
                if (
                    jid?.endsWith("@broadcast") &&
                    !CONFIG.lerBroadcasts
                ) continue;

                // Conversas individuais
                const conversaIndividual =
                    jid?.endsWith("@lid") ||
                    jid?.endsWith("@s.whatsapp.net");

                if (
                    conversaIndividual &&
                    !CONFIG.lerContatos
                ) continue;
                const numero =
                    msg.key.remoteJidAlt ||
                    msg.key.participantAlt ||
                    msg.key.remoteJid;

                const dadosMensagem = extrairMensagem(msg);

                onMensagem({

                    numero: numero.split("@")[0],

                    nome: msg.pushName ?? "",

                    tipo: dadosMensagem.tipo,

                    mensagem: dadosMensagem.mensagem,

                    timestamp:
                        Number(msg.messageTimestamp) * 1000

                });

            }

        });

    });

}

/*
|--------------------------------------------------------------------------
| Envia mensagem
|--------------------------------------------------------------------------
*/

export async function enviarMensagem(numero, mensagem) {

    if (!sock)
        throw new Error("WhatsApp não conectado.");

    numero = numero.replace(/\D/g, "");

    await sock.sendMessage(
        `${numero}@s.whatsapp.net`,
        {
            text: mensagem
        }
    );

}