import os
import time
import logging
import requests
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
TOKEN = "053d49f28385aa3f0ca96e7ba20e2f6d"

# Função para consultar o clima atual de uma cidade, caso o valor cidade não seja passado sempre consulta São Paulo
def consultar_clima(cidade="São Paulo", pais="BR"):
    # Monta a URL da requisição (formato: cidade,país)
    url = "https://api.openweathermap.org/data/2.5/weather"

    # Cabeçalho (não é obrigatório para esta API, mas como boa prática resolvi colocar)
    headers = {
        "Accept": "application/json"
    }

    # Parâmetros da URL
    params = {
        "q": f"{cidade},{pais}",     # Nome da cidade e país (ex: "São Paulo,BR")
        "appid": TOKEN,            # Chave de acesso
        "units": "metric",           # Retorna temperatura em Celsius
        "lang": "pt_br"              # Retorna descrições em português
    }
    
    logger.info(f"\nConsultando clima de: {cidade} - {pais}")
    logger.info(f"Parâmetros: {params}")

    try:
        # Envia a requisição GET com parâmetros
        resposta = requests.get(url, headers=headers, params=params, timeout=30)
        logger.info(f"Status Code: {resposta.status_code}")

        if resposta.status_code == 200:
            dados = resposta.json()  # Converte a resposta JSON em dicionário

            # Extrai dados principais
            info = {
                "cidade": dados["name"],
                "temperatura": dados["main"]["temp"],
                "sensacao_termica": dados["main"]["feels_like"],
                "temperatura_min": dados["main"]["temp_min"],
                "temperatura_max": dados["main"]["temp_max"],
                "umidade": dados["main"]["humidity"],
                "clima": dados["weather"][0]["description"],
                "velocidade_vento": dados["wind"]["speed"],
                "data_hora": pd.Timestamp.now()
            }

            logger.info("Dados extraídos com sucesso!")
            return pd.DataFrame([info]), True

        elif resposta.status_code == 401:
            logger.warning("Erro 401: API key inválida ou ausente.")
        elif resposta.status_code == 404:
            logger.warning("Erro 404: Cidade não encontrada.")
        else:
            logger.error(f"Erro {resposta.status_code}: {resposta.text}")

        return pd.DataFrame(), False

    except requests.exceptions.RequestException as erro:
        logger.error(f"Exceção: {erro}")
        return pd.DataFrame(), False

# Executa o script principal
if __name__ == "__main__":

    # Captura o momento atual no início da execução
    agora = datetime.now()

    # Formata o nome do arquivo com data e hora
    nome_arquivo = agora.strftime("api_tempo_%d%m%Y_%H%M%S.log")
    # Cria o arquivo de Log
    configurar_logging(nome_arquivo)
    logger = logging.getLogger(__name__)
    
    # Pode-se passar quantas cidades forem necessárias seguindo o mesmo padrão
    cidades = [
        ("São Paulo", "BR"),
        ("Rio de Janeiro", "BR"),
        ("Jundiaí", "BR"),
        ("Cambuí", "BR")
    ]

    clima_total = pd.DataFrame()
    # Percorre todas as cidades a serem consultadas
    for cidade, pais in cidades:
        df, ok = consultar_clima(cidade, pais)
        if ok:
            clima_total = pd.concat([clima_total, df], ignore_index=True)
        time.sleep(1)  # Evita limite de requisição da API gratuita

    # Exporta resultados para CSV
    if not clima_total.empty:
        clima_total.to_csv("clima_atual.csv", index=False, encoding="utf-8-sig", sep=";")
        logger.info("\nArquivo 'clima_atual.csv' salvo com sucesso!")
    else:
        logger.warning("\nNenhum dado foi coletado. Verifique sua API key ou cidades.")
