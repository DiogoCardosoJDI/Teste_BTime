import os
import time
import requests
import logging
import pandas as pd
from datetime import datetime

def configurar_logging(nome_arquivo_log="consulta_api_tempo.log", nivel=logging.INFO):
    os.makedirs("logs", exist_ok=True)  # Cria pasta se não existir

    caminho_log = os.path.join("logs", nome_arquivo_log)

    logging.basicConfig(
        filename=caminho_log,
        level=nivel,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filemode='a'  # ou 'w' para sobrescrever cada vez
    )

    # Também mostra no terminal:
    console = logging.StreamHandler()
    console.setLevel(nivel)
    console.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    logging.getLogger().addHandler(console)  

# Chave da API
TOKEN = "6b29b82bfacc4e7a9efc6b7273b12a7d"

# Função para consultar partidas de uma competição específica em uma determinada temporada, caso competicao_id esteja vazio por padrão carrega dados do Brasileirão
def consultar_partidas(competicao_id="BSA", temporada=2024, pagina=1):
    # URL do endpoint da API para buscar partidas de uma competição
    url = f"https://api.football-data.org/v4/competitions/{competicao_id}/matches"

    # Cabeçalho com a chave de autenticação exigida pela API
    headers = {
        "X-Auth-Token": TOKEN,               # Autenticação via token
        "Accept": "application/json"         # Requisição em formato JSON
    }

    # Parâmetros da requisição: temporada e paginação
    params = {
        "season": temporada,
        "page": pagina
    }
    # Exibe informações para debug
    logger.info(f"\n➡️ Página {pagina} | Consultando: {url}")
    logger.info(f"   Parâmetros: {params}")

    try:
        # Envia a requisição GET para a API
        resposta = requests.get(url, headers=headers, params=params, timeout=30)
        logger.info(f"   Status Code: {resposta.status_code}")  # Mostra o código da resposta

        # Caso a resposta seja bem-sucedida (200 OK)
        if resposta.status_code == 200:
            dados = resposta.json()                       # Converte resposta em dicionário
            matches = dados.get("matches", [])            # Extrai a lista de partidas
            if not matches:
                logger.info("Nenhuma partida encontrada.")
                return pd.DataFrame(), False              # Retorna DataFrame vazio se não houver partidas
            return pd.DataFrame(matches), True            # Retorna os dados em formato de tabela
        elif resposta.status_code == 403:
            logger.warning("Erro 403: Token inválido ou sem permissão.")
        elif resposta.status_code == 429:
            logger.warning("Erro 429: Limite de requisições excedido.")
        else:
            logger.error(f"Erro {resposta.status_code}: {resposta.text}")

        return pd.DataFrame(), False
    
    except requests.exceptions.RequestException as erro:
        # Captura exceções de rede ou requisição
        logger.error(f"Exceção: {erro}")
        return pd.DataFrame(), False

# Executa o script principal
if __name__ == "__main__":

    # Captura o momento atual no início da execução
    agora = datetime.now()

    # Formata o nome do arquivo com data e hora
    nome_arquivo = agora.strftime("api_sport_%d%m%Y_%H%M%S.log")
    # Cria o arquivo de Log
    configurar_logging(nome_arquivo)
    logger = logging.getLogger(__name__)

    competicao_id = "BSA"      # Código do Brasileirao serie A (pode trocar por PL, CL, PD, etc.)
    temporada = 2024          # Temporada desejada
    pagina = 1                # Página inicial
    todos_os_jogos = pd.DataFrame()  # DataFrame acumulador para armazenar todos os jogos

    # Loop para buscar todas as páginas de partidas
    while True:
        df, has_data = consultar_partidas(competicao_id, temporada, pagina)
        if df.empty or not has_data:
            break                                 # Sai do loop se não houver mais dados
        todos_os_jogos = pd.concat([todos_os_jogos, df], ignore_index=True)  # Acumula os dados
        pagina += 1                               # Vai para próxima página
        time.sleep(1)                             # Aguarda 1 segundo para evitar limite de requisições

    # Exporta os dados para CSV se houver partidas
    if not todos_os_jogos.empty:
        todos_os_jogos.to_csv("partidas_brasileirao_2024.csv", index=False, encoding="utf-8-sig", sep=";")
        logger.info("\nCSV salvo com sucesso!")
    else:
        logger.info("\nNenhuma partida foi retornada da API.")
