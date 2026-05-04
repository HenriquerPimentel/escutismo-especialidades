import requests
import urllib.parse
from bs4 import BeautifulSoup
import json
import time
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36"
}

class Area:
    def __init__(self, titulo, imagem):
        self.titulo = titulo
        self.imagem = imagem
    def to_dict(self):
        return {"titulo": self.titulo, "imagem": self.imagem}

class Provas:
    def __init__(self, seccao, base, avancado):
        self.seccao = seccao
        self.base = base
        self.avancado = avancado
    def to_dict(self):
        return {"seccao": self.seccao, "base": self.base, "avancado": self.avancado}

class Especialidade:
    def __init__(self, titulo, descricao, imagem, areas, provas):
        self.titulo = titulo
        self.descricao = descricao
        self.imagem = imagem
        self.areas = areas
        self.provas = provas
    def to_dict(self):
        return {
            "titulo": self.titulo, "descricao": self.descricao, "imagem": self.imagem,
            "areas": [a.to_dict() for a in self.areas], "provas": [p.to_dict() for p in self.provas]
        }

def obter_urls_especialidades():
    url_principal = "https://especialidades.escutismo.pt/especialidades-2/"
    print("A aceder ao site principal para obter a lista de URLs...")
    
    resposta = requests.get(url_principal, headers=HEADERS)
    resposta.raise_for_status()
    sopa = BeautifulSoup(resposta.text, 'html.parser')
    
    urls = []
    figuras = sopa.find_all('figure', class_='wp-caption')
    
    for fig in figuras:
        link_tag = fig.find('a', href=True)
        if link_tag:
            url = link_tag['href']
            if "s=vigi" in url:
                url = "https://especialidades.escutismo.pt/vigilante-da-natureza/"
                
            if url not in urls and "escutismo.pt" in url:
                urls.append(url)
                
    return urls

def extrair_dados_especialidade(url):
    try:
        resposta = requests.get(url, headers=HEADERS)
        resposta.raise_for_status()
        sopa = BeautifulSoup(resposta.text, 'html.parser')
        
        main_content = sopa.find('main')
        if not main_content:
            main_content = sopa
            
        titulo = ""
        tag_titulo = main_content.find(['h1', 'h2'], class_='elementor-heading-title')
        if tag_titulo:
            titulo = tag_titulo.get_text(strip=True)
            
        if not titulo or titulo == "Sem Título":
            tag_head_title = sopa.find('title')
            if tag_head_title:
                texto_separador = tag_head_title.get_text(strip=True)
                titulo = re.split(r'[-–|]', texto_separador)[0].strip()
                
        if not titulo:
            titulo = "Sem Título"
        
        imagem_url = ""
        img_widget = main_content.find('div', class_='elementor-widget-image')
        if img_widget and img_widget.find('img'):
            imagem_url = img_widget.find('img').get('src', '')
                
        descricao = ""
        desc_widget = main_content.find('div', class_='elementor-widget-text-editor')
        if desc_widget:
            descricao = desc_widget.get_text(strip=True)
                
        provas_lista = []
        seccoes_nomes = ["Primeira Secção", "Segunda Secção", "Terceira Secção", "Quarta Secção"]
        
        for sec_nome in seccoes_nomes:
            h2_sec = main_content.find(['h2', 'h3', 'h4'], string=lambda t: t and sec_nome in t)
            if h2_sec:
                base_h2 = h2_sec.find_next(['h2', 'h3', 'h4', 'p'], string=lambda t: t and 'Base' in t)
                base_reqs = []
                if base_h2:
                    ul_base = base_h2.find_next('ul')
                    if ul_base:
                        base_reqs = [li.get_text(strip=True) for li in ul_base.find_all('li')]
                
                avancado_h2 = h2_sec.find_next(['h2', 'h3', 'h4', 'p'], string=lambda t: t and 'Avançado' in t)
                avancado_reqs = []
                if avancado_h2:
                    ul_avancado = avancado_h2.find_next('ul')
                    if ul_avancado:
                        avancado_reqs = [li.get_text(strip=True) for li in ul_avancado.find_all('li')]
                
                provas_lista.append(Provas(seccao=sec_nome, base=base_reqs, avancado=avancado_reqs))

        areas_lista = []
        colunas_20 = main_content.find_all('div', class_='elementor-col-20')
        for col in colunas_20:
            img_tag = col.find('img')
            if img_tag:
                src = img_tag.get('src', '')
                nome_arquivo = src.split('/')[-1]
                nome_limpo = urllib.parse.unquote(nome_arquivo)
                nome_limpo = nome_limpo.replace('.png', '').replace('.jpg', '').replace('-', ' ')
                nome_limpo = re.sub(r'-\d+x\d+', '', nome_limpo)
                areas_lista.append(Area(titulo=nome_limpo.strip(), imagem=src))

        return Especialidade(titulo, descricao, imagem_url, areas_lista, provas_lista)

    except Exception as e:
        print(f"  [ERRO] Falha ao extrair {url}: {e}")
        return None

def main():
    urls = obter_urls_especialidades()
    total = len(urls)
    print(f"Foram encontrados {total} links de especialidades.\n")
    
    livro_especialidades = []
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{total}] A extrair dados de: {url}")
        especialidade = extrair_dados_especialidade(url)
        if especialidade:
            livro_especialidades.append(especialidade.to_dict())
        time.sleep(1)
        
    nome_ficheiro = "especialidades.json"
    with open(nome_ficheiro, 'w', encoding='utf-8') as f:
        json.dump(livro_especialidades, f, ensure_ascii=False, indent=4)
        
    print("\nProcesso finalizado!")

if __name__ == "__main__":
    main()