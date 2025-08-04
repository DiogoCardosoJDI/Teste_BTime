import os
import time
import random
import logging
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def configurar_logging(nome_arquivo_log="web_scraping.log", nivel=logging.INFO):
    # Cria pasta se não existir
    os.makedirs("logs", exist_ok=True)

    caminho_log = os.path.join("logs", nome_arquivo_log)

    logging.basicConfig(
        filename=caminho_log,
        level=nivel,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        # ou 'w' para sobrescrever cada vez
        filemode='a'
    )

    # Também mostra no terminal:
    console = logging.StreamHandler()
    console.setLevel(nivel)
    console.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    logging.getLogger().addHandler(console)    

# Função para configurar e iniciar o navegador em modo headless (sem interface gráfica), caso queira ver somente comentar o argumento headless
def iniciar_driver():
    logger.info("Iniciando a configuração para acessar a web")
    options = Options()
    # Executa sem abrir o navegador visivelmente
    options.add_argument("--headless")
    # Necessário em ambientes Linux restritos
    options.add_argument("--no-sandbox")
    # Evita erros em alguns sistemas
    options.add_argument("--disable-gpu")
    logger.info("Fim da configuração para acessar a web, retornando objeto")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Função para extrair dados de livros de uma única página
def extrair_dados_pagina(soup):
    livros = []
    # Cada livro está dentro de uma <article>
    artigos = soup.find_all('article', class_='product_pod')

    for artigo in artigos:
        # O título do livro está no atributo 'title'
        titulo = artigo.h3.a['title']
        # Remove o símbolo da libra
        preco = artigo.find('p', class_='price_color').text.strip().replace('£', '')
        # Ex: "In stock"
        disponibilidade = artigo.find('p', class_='instock availability').text.strip()
        # A segunda classe da tag <p> contém a classificação (ex: 'Three')
        classificacao = artigo.p['class'][1]

        livros.append({
            "titulo": titulo,
            "preco_libras": preco,
            "disponibilidade": disponibilidade,
            "classificacao": classificacao
        })
    # Retorna um dicionário com os dados dos livros
    return livros

# Função principal que controla a coleta de várias páginas
def realizar_scraping():
    # URL base com paginação
    url_base = "http://books.toscrape.com/catalogue/page-{}.html"
    # Inicia o navegador
    chrome = iniciar_driver()
    # Lista para armazenar todos os dados coletados
    dados_completos = []

    try:
        # Loop pelas páginas (nesse exemplo, da 1 até a 5)
        for pagina in range(1, 6):
            logger.info(f"Coletando página {pagina}...")
            # Acessa a página
            chrome.get(url_base.format(pagina))
            # Aguarda de forma aleatória para parecer mais humano
            time.sleep(random.uniform(1.5, 3.5))

            # Pega o HTML da página e transforma em objeto BeautifulSoup
            soup = BeautifulSoup(chrome.page_source, "html.parser")
            # Extrai os dados da página
            dados = extrair_dados_pagina(soup)
            # Adiciona os dados à lista principal
            dados_completos.extend(dados)

        # Cria DataFrame e exporta para CSV
        logger.info("Criando DataFrame e exportando para CSV")
        df = pd.DataFrame(dados_completos)
        
        # Abre o arquivo CSV manualmente e escreve linha por linha para evitar erro na tabulação dos dados
        with open("dados_final.csv", "w", encoding="utf-8", newline="") as arquivo:
            # Escreve o cabeçalho manualmente
            arquivo.write('"titulo","preco_libras","disponibilidade","classificacao"\n')

            # Escreve linha por linha com todos os campos entre aspas para evitar quebra das informações
            logger.info("Escrevendo linha por linha no csv")
            for linha in dados_completos:
                # escapa aspas duplas se houver
                titulo = linha["titulo"].replace('"', '""')
                preco = linha["preco_libras"]
                disponibilidade = linha["disponibilidade"]
                classificacao = linha["classificacao"]

                linha_csv = f'{titulo};{preco};{disponibilidade};{classificacao}\n'

                arquivo.write(linha_csv)


        logger.info("Scraping finalizado com sucesso. Arquivo 'dados_final.csv' gerado.")
       
    except Exception as e:
        # Captura e exibe erros, caso ocorram
        logger.error(f"Erro durante o scraping: {e}")

    finally:
        # Garante que o navegador será fechado mesmo se houver erro
        chrome.quit()

# Ponto de entrada principal do script
if __name__ == "__main__":

    # Captura o momento atual no início da execução
    agora = datetime.now()

    # Formata o nome do arquivo com data e hora
    nome_arquivo = agora.strftime("web_scrap_%d%m%Y_%H%M%S.log")

    # Cria o arquivo de Log
    configurar_logging(nome_arquivo)
    logger = logging.getLogger(__name__)
    realizar_scraping()
