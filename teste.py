import time
import threading
import os
from google import genai
from google.genai import types

# =====================================================================
# 1. CONFIGURAÇÃO DA API DO GEMINI
# =====================================================================
API_KEY = "AQ.Ab8RN6L5z9ZhbG-0wP9ufEdl5Ux-15IPXd9TeH-OIC4H4s_44g"
client = genai.Client(api_key=API_KEY)

def classificar_com_gemini(texto_cliente):
    """Envia o texto complexo acumulado para o Gemini classificar"""
    prompt = f"""
    Você é um assistente de clínica médica responsável por gerenciar a agenda.
    Classifique a resposta do paciente sobre a confirmação da consulta de amanhã.
    
    Regras estritas de resposta: Devolva APENAS uma das três palavras abaixo, em maiúsculo, sem pontos, espaços extras ou explicações:
    - CONFIRMADO: se o cliente confirmou explicitamente que vai (ex: "vou sim", "com certeza", "pode marcar").
    - CANCELADO: se o cliente disse claramente que não vai ou quer desmarcar (ex: "não posso", "cancela", "infelizmente não vou").
    - HUMANO: se o cliente fez uma pergunta, demonstrou dúvida ou a resposta exige que a secretária leia (ex: "aceita convênio?", "pode ser mais tarde?", "posso levar acompanhante?", "queria tirar uma dúvida").

    Resposta do paciente: "{texto_cliente}"
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"ERRO NA API: {e}"

# =====================================================================
# 2. CADEIA DE LEITURA (HEURÍSTICA LOCAL VS INTEGRAÇÃO COM IA)
# =====================================================================
def analisar_resposta_completa(texto_cliente):
    """Cadeia de leitura otimizada para economizar tokens antes de decidir chamar a IA"""
    texto_limpo = texto_cliente.strip().lower()
    
    # Etapa 1: Filtro Heurístico Local (Custo 0)
    if texto_limpo in ['sim', 's', 'vou', 'ok', 'confirmado', 'combinado', 'blz', '👍', '👌']:
        return "CONFIRMADO"
        
    if texto_limpo in ['não', 'nao', 'n', 'cancela', 'não vou', '👎']:
        return "CANCELADO"
        
    if texto_limpo == "[áudio]":
        return "HUMANO"
        
    # Etapa 2: Se for um bloco complexo ou inconclusivo localmente, aciona a IA
    # Nota: O sleep de 12s foi comentado aqui no motor assíncrono para os testes de debounce fluírem no tempo certo.
    # print("🤖 Resposta complexa ou emoji novo. Aguardando 12s para respeitar o limite grátis da API...")
    time.sleep(12) 
    
    resultado_ia = classificar_com_gemini(texto_cliente)
    return resultado_ia

# =====================================================================
# 3. CONTROLE DE ESTADO E BUFFER (ESTRUTURA DE PRECAUÇÃO DE MENSAGENS)
# =====================================================================
# Guarda o estado atual da agenda da clínica
banco_agenda_clinica = {
    "5527999999999": "Aguardando Confirmação"
}

# Buffer temporário para agrupar as mensagens picadas por número de telefone
buffer_mensagens = {}

def receber_mensagem_webhook(numero_cliente, texto_mensagem):
    """Filtro de entrada: Intercepta e acumula as mensagens vindas do WhatsApp"""
    agora = time.time()
    janela_espera = 15  # Tempo (segundos) que aguardamos o cliente terminar de digitar

    # Passo 1: Validação de Estado (Garante que paramos assim que houver um veredito conclusivo)
    status_atual = banco_agenda_clinica.get(numero_cliente, "Não Encontrado")
    
    if status_atual in ["CONFIRMADO", "CANCELADO"]:
        print(f"\n[Filtro] Mensagem de {numero_cliente} IGNORADA no WhatsApp. Agendamento já está como: {status_atual}.")
        return

    # Passo 2: Lógica de Debounce (Agrupamento Temporal)
    if numero_cliente not in buffer_mensagens:
        buffer_mensagens[numero_cliente] = {
            "texto": texto_mensagem,
            "limite_tempo": agora + janela_espera
        }
        print(f"\n[Buffer] Nova mensagem de {numero_cliente}: '{texto_mensagem}'. Aguardando {janela_espera}s de silêncio...")
    else:
        buffer_mensagens[numero_cliente]["texto"] += " " + texto_mensagem
        buffer_mensagens[numero_cliente]["limite_tempo"] = agora + janela_espera
        print(f"[Buffer] Mensagem picada de {numero_cliente}: '{texto_mensagem}'. Bloco acumulado: '{buffer_mensagens[numero_cliente]['texto']}'. Resetando cronômetro para +{janela_espera}s.")

# =====================================================================
# 4. MOTOR DA FILA AS SÍNCRONO (RODA EM SEGUNDO PLANO)
# =====================================================================
def monitorar_fila_de_espera():
    """Varre constantemente o buffer procurando por janelas de silêncio finalizadas"""
    while True:
        agora = time.time()
        numeros_para_processar = []

        for numero, dados in list(buffer_mensagens.items()):
            # Se o paciente ficou 15 segundos sem enviar nada novo, processa o bloco completo
            if agora >= dados["limite_tempo"]:
                numeros_para_processar.append(numero)
                texto_final = dados["texto"]
                
                print(f"\n[Fila] ⏱️ Janela de silêncio de {numero} esgotada! Analisando bloco total recebido...")
                
                # Executa a nossa cadeia lógica inteligente
                veredito = analisar_resposta_completa(texto_final)
                
                # Decisão de negócios com base no resultado da IA / Heurística
                if veredito in ["CONFIRMADO", "CANCELADO"]:
                    banco_agenda_clinica[numero] = veredito
                    print(f"🏆 [AGENDA ATUALIZADA NO VISOR] Paciente {numero} -> {veredito}")
                elif veredito == "HUMANO":
                    print(f"⚠️ [TRANSBORDO HUMANO] Paciente {numero} precisa de atenção humana. Texto enviado: '{texto_final}'")
                else:
                    # Caso retorne inconclusivo ou erro de API, mantemos a porteira aberta para a próxima mensagem
                    print(f"🔄 [REPOSTA INCOMPLETA/ERRO] Veredito: {veredito}. Mantendo porteira aberta para novas mensagens.")

        # Limpa da memória os números que já saíram da fila de espera
        for numero in numeros_para_processar:
            del buffer_mensagens[numero]

        time.sleep(0.5)

# =====================================================================
# 5. SIMULADOR DO CENÁRIO DE TESTE INTEGRADO
# =====================================================================
if __name__ == "__main__":
    # Inicializa o motor de monitoramento em uma Thread separada (background)
    threading.Thread(target=monitorar_fila_de_espera, daemon=True).start()
    
    paciente_teste = "5527999999999"
    
    print("=== INICIANDO SIMULADOR DE FLUXO INTEGRADO ===")
    print(f"Status Inicial do Paciente: {banco_agenda_clinica[paciente_teste]}")
    
    # -----------------------------------------------------------------
    # SIMULAÇÃO 1: Usuário manda mensagens picadas e indecisas ("Espera que vou ver")
    # -----------------------------------------------------------------
    receber_mensagem_webhook(paciente_teste, "Oi, boa noite!")
    time.sleep(3)
    receber_mensagem_webhook(paciente_teste, "espera que vou ver com o meu chefe se posso sair mais cedo")
    
    # Aguarda 17 segundos para estourar o tempo. O motor vai processar, bater na IA, 
    # e como o texto é indeciso, vai manter a porteira aberta sem atualizar para CONFIRMADO/CANCELADO.
    time.sleep(17)
    
    # -----------------------------------------------------------------
    # SIMULAÇÃO 2: Usuário retorna depois de um tempo e manda a resposta definitiva em partes
    # -----------------------------------------------------------------
    receber_mensagem_webhook(paciente_teste, "Pronto, consegui falar com ele!")
    time.sleep(4)
    receber_mensagem_webhook(paciente_teste, "vou sim")
    time.sleep(2)
    receber_mensagem_webhook(paciente_teste, "pode confirmar amanhã 👍")
    
    # Aguarda 17 segundos para o motor fechar a segunda janela. Agora vai bater o martelo de CONFIRMADO.
    time.sleep(17)
    
    # -----------------------------------------------------------------
    # SIMULAÇÃO 3: Paciente tenta mandar algo extra após o robô já ter decidido e encerrado
    # -----------------------------------------------------------------
    receber_mensagem_webhook(paciente_teste, "Qual o endereço mesmo?")
    
    time.sleep(2)
    print(f"\nStatus Final da Agenda da Clínica: {banco_agenda_clinica[paciente_teste]}")
    print("=== FIM DO TESTE ===")