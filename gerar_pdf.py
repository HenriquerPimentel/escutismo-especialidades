import json
import argparse
import re
import unicodedata
import textwrap
import os
import requests
from datetime import datetime
from fpdf import FPDF
from pypdf import PdfWriter, PdfReader

COR_UNICA = (80, 46, 18)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
CAPA_PATH = os.path.join(ASSETS_DIR, "capa.pdf")

def limpar_texto(texto):
    if not texto:
        return ""
    texto = re.sub(r'\s+', ' ', texto)
    texto = unicodedata.normalize('NFC', texto)
    substituicoes = {
        '–': '-', '—': '-', '"': '"', '"': '"',
        "'": "'", "'": "'", '…': '...', '•': '-',
        'º': 'o', 'ª': 'a', '´': "'", '`': "'"
    }
    for velho, novo in substituicoes.items():
        texto = texto.replace(velho, novo)
    texto = texto.encode('latin-1', 'ignore').decode('latin-1')
    return texto.strip()

def padronizar_area(nome_area):
    n = nome_area.lower()
    if "placeholder" in n:
        return None
    if "cinecia" in n or "ciência" in n or "ciencia" in n:
        return "Ciências e tecnologia"
    if "comunica" in n:
        return "Comunicação, informação e relacionamento"
    if "físico" in n or "fisico" in n:
        return "Desenvolvimento físico"
    if "religi" in n:
        return "Fé e Religião"
    if "vida profissional" in n or "cratividade" in n or "criatividade" in n:
        return "Habilidade, criatividade e vida profissional"
    if "natureza" in n or "campo" in n:
        return "Natureza, ambiente e vida em campo"
    if "socorrismo" in n or "serviço" in n or "servico" in n:
        return "Serviço e socorrismo"
    if "terra" in n or "água" in n or "agua" in n:
        return "Terra, água e ar"
    return limpar_texto(nome_area)

def escrever_texto_seguro(pdf, texto, largura_max=95, altura_linha=6, alinhamento="L"):
    if not texto:
        pdf.ln(altura_linha)
        return
    if alinhamento == "J":
        pdf.multi_cell(0, altura_linha, texto, align="J")
        return
    linhas = textwrap.wrap(texto, width=largura_max)
    for linha in linhas:
        pdf.cell(0, altura_linha, linha, new_x="LMARGIN", new_y="NEXT", align=alinhamento)


def escrever_texto_markup_atomic(pdf, texto, largura_max=95, altura_linha=6, alinhamento="L"):
    if not texto:
        pdf.ln(altura_linha)
        return
    available_width = pdf.w - pdf.l_margin - pdf.r_margin
    if alinhamento == "J" and "*" not in texto:
        pdf.multi_cell(0, altura_linha, texto, align="J")
        return
    partes = re.split(r'(\*.+?\*)', texto)
    tokens = []
    for p in partes:
        if not p:
            continue
        if p.startswith('*') and p.endswith('*'):
            tokens.append((p[1:-1], True))
        else:
            words = re.findall(r"\S+\s*", p)
            for w in words:
                tokens.append((w, False))
    x_start = pdf.l_margin
    y = pdf.get_y()
    x = x_start
    for text, is_bold in tokens:
        aplicar_fonte(pdf, "Avenir-Bold" if is_bold else "Avenir-Regular", 10)
        w = pdf.get_string_width(text)
        if (x - x_start + w) > available_width:
            pdf.ln(altura_linha)
            y = pdf.get_y()
            x = x_start
        pdf.set_xy(x, y)
        pdf.cell(w + 0.5, altura_linha, text, new_x="RIGHT")
        x = pdf.get_x()
    pdf.ln(altura_linha)

def aplicar_fonte(pdf, familia, tamanho):
    try:
        pdf.set_font(familia, "", tamanho)
    except:
        pdf.set_font("helvetica", "", tamanho)

def baixar_imagem_local(url, ficheiro_local):
    if os.path.exists(ficheiro_local):
        return ficheiro_local
    try:
        resposta = requests.get(url, timeout=10)
        if resposta.status_code == 200:
            with open(ficheiro_local, "wb") as f_img:
                f_img.write(resposta.content)
            return ficheiro_local
    except:
        pass
    return None

class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_text_color(*COR_UNICA)
        aplicar_fonte(self, "Avenir-Regular", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

IMAGENS_CACHE = {}

def filtrar_especialidades_por_secao(dados, section_num):
    if section_num is None:
        return dados
    mapa_secoes = {1: "Primeira Secção", 2: "Segunda Secção", 3: "Terceira Secção", 4: "Quarta Secção"}
    secao_nome = mapa_secoes.get(section_num)
    if not secao_nome:
        return dados
    dados_filtrados = []
    for esp in dados:
        esp_copia = esp.copy()
        provas_filtradas = []
        for prova in esp.get("provas", []):
            if prova.get("seccao") == secao_nome:
                provas_filtradas.append(prova)
        esp_copia["provas"] = provas_filtradas
        if provas_filtradas:
            dados_filtrados.append(esp_copia)
    return dados_filtrados

def gerar_ficha_tecnica(pdf):
    hoje = datetime.now()
    meses_pt = {1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho", 7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}
    data_str = f"{hoje.day} de {meses_pt[hoje.month]} de {hoje.year}"
    hora_str = hoje.strftime("%H:%M")
    pdf.add_page()
    pdf.set_text_color(*COR_UNICA)
    aplicar_fonte(pdf, "Lilita", 24)
    pdf.cell(0, 20, "Ficha Técnica", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)
    aplicar_fonte(pdf, "Avenir-Regular", 12)
    aplicar_fonte(pdf, "Avenir-Bold", 12)
    pdf.cell(0, 8, "Título:", new_x="LMARGIN", new_y="NEXT", align="L")
    aplicar_fonte(pdf, "Avenir-Regular", 11)
    pdf.cell(0, 8, "Sistema de Especialidades", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(5)
    aplicar_fonte(pdf, "Avenir-Bold", 12)
    pdf.cell(0, 8, "Data de extração:", new_x="LMARGIN", new_y="NEXT", align="L")
    aplicar_fonte(pdf, "Avenir-Regular", 11)
    pdf.cell(0, 8, f"{data_str} às {hora_str}", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(5)
    aplicar_fonte(pdf, "Avenir-Bold", 12)
    pdf.cell(0, 8, "Fonte:", new_x="LMARGIN", new_y="NEXT", align="L")
    aplicar_fonte(pdf, "Avenir-Regular", 11)
    pdf.cell(0, 8, "especialidades.escutismo.pt", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(5)
    aplicar_fonte(pdf, "Avenir-Bold", 12)
    pdf.cell(0, 8, "Geração automática:", new_x="LMARGIN", new_y="NEXT", align="L")
    aplicar_fonte(pdf, "Avenir-Regular", 11)
    escrever_texto_seguro(pdf, "Este documento foi gerado automaticamente através de um script, disponível em https://github.com/HenriquerPimentel/escutismo-especialidades", largura_max=90, altura_linha=6, alinhamento="L")
    pdf.ln(8)
    aplicar_fonte(pdf, "Avenir-Bold", 12)
    pdf.cell(0, 8, "Direitos de Imagem:", new_x="LMARGIN", new_y="NEXT", align="L")
    aplicar_fonte(pdf, "Avenir-Regular", 11)
    escrever_texto_seguro(pdf, "Os ícones e logótipos das especialidades são propriedade do Corpo Nacional de Escutas (CNE).", largura_max=90, altura_linha=6, alinhamento="L")

def compilar_pdf(dados, mapa_paginas=None, is_final=False, section_num=None, mapa_imagens_areas=None):
    """
    Esta função é corrida 2 vezes:
    1ª vez: Sem mapa de páginas. Gera o PDF às cegas apenas para descobrir em que página calha cada especialidade.
    2ª vez: Recebe o mapa. Gera o PDF final escrevendo as páginas exatas nos índices.
    section_num: None (todas as secções), 1-4 (apenas essa secção de provas)
    mapa_imagens_areas: Dicionário mapeando nomes de áreas padronizadas -> URLs de imagens
    """
    # Filtrar provas por secção se especificado
    if section_num is not None:
        dados = filtrar_especialidades_por_secao(dados, section_num)
        mapa_secoes = {1: "Primeira Secção", 2: "Segunda Secção", 3: "Terceira Secção", 4: "Quarta Secção"}
        if is_final:  # Print only once
            print(f" -> Filtradas {len(dados)} especialidades com provas de {mapa_secoes.get(section_num)}")
    
    if mapa_paginas is None:
        mapa_paginas = {}
        
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Carregar Fontes
    lilita_path = os.path.join(FONTS_DIR, "LilitaOne-Regular.ttf")
    avenir_regular_path = os.path.join(FONTS_DIR, "AvenirNext-Regular-08.ttf")
    avenir_bold_path = os.path.join(FONTS_DIR, "AvenirNext-Bold-01.ttf")

    if os.path.exists(lilita_path):
        pdf.add_font("Lilita", "", lilita_path, uni=True)
    if os.path.exists(avenir_regular_path):
        pdf.add_font("Avenir-Regular", "", avenir_regular_path, uni=True)
    if os.path.exists(avenir_bold_path):
        pdf.add_font("Avenir-Bold", "", avenir_bold_path, uni=True)
        
    
    gerar_ficha_tecnica(pdf)

    pdf.add_page()
    pdf.set_text_color(*COR_UNICA)
    aplicar_fonte(pdf, "Lilita", 22)
    pdf.cell(0, 14, "Como funcionam as especialidades", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    aplicar_fonte(pdf, "Lilita", 12)
    pdf.cell(0, 8, "ESPECIALIDADES", new_x="LMARGIN", new_y="NEXT", align="L")
    aplicar_fonte(pdf, "Avenir-Regular", 10)
    texto_especialidades = [
        "As especialidades constituem oportunidades de desenvolvimento pessoal, sendo – sempre que possível e aplicável – transversais a todas as secções e o mais variadas possível, de modo a ir de encontro à diversidade e extensão dos interesses pessoais de cada criança e jovem.",
        "As especialidades podem começar a ser trabalhadas assim que a criança ou jovem, tendo concluído a etapa de adesão – Pata-Tenra, Apelo, Desprendimento ou Caminho – faça a sua Promessa.",
        "O objectivo é que cada criança ou jovem desenvolva as suas capacidades e se torne, realmente, habilitado em determinada temática, pelo que a obtenção de uma especialidade, e ainda mais a sua continuidade ao longo das secções, deve ser encarada numa perspectiva de aprofundamento e não apenas como uma aquisição superficial de alguns conceitos."
    ]
    for p in texto_especialidades:
        escrever_texto_seguro(pdf, p, largura_max=90, altura_linha=7, alinhamento="J")
        pdf.ln(3)

    pdf.ln(4)
    aplicar_fonte(pdf, "Lilita", 12)
    pdf.cell(0, 8, "ÁREAS", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(2)

    imagem_areas = baixar_imagem_local(
        "https://especialidades.escutismo.pt/wp-content/uploads/sites/18/2021/07/Areas.jpg",
        "img_areas.jpg"
    )

    aplicar_fonte(pdf, "Avenir-Regular", 10)
    texto_areas = (
        "As especialidades estão agrupadas em oito conjuntos temáticos de propostas de especialidades, relacionadas entre si.\n\n"
        "Para se alcançar uma especialidade, é necessário cumprir os seis requisitos estipulados, divididos em dois grupos: requisitos base e requisitos avançados, em que os requisitos avançados duma Secção compõem os requisitos base da Secção seguinte (onde aplicável).\n\n"
        "A qualificação é da competência do Conselho de Guias e é exarada em Ordem de Serviço de Agrupamento e registada obrigatoriamente no SIIE."
    )

    
    # Escrever texto em coluna única
    escrever_texto_seguro(pdf, texto_areas, largura_max=90, altura_linha=6, alinhamento="J")
    pdf.ln(4)

    # Inserir imagem abaixo do texto, centrada
    if imagem_areas and os.path.exists(imagem_areas):
        try:
            pdf.image(imagem_areas, x="C", w=120)
            pdf.ln(6)
        except:
            pass

    pdf.ln(4)
    aplicar_fonte(pdf, "Lilita", 12)
    pdf.cell(0, 8, "COLOCAÇÃO DAS INSÍGNIAS DE ESPECIALIDADES", new_x="LMARGIN", new_y="NEXT", align="L")
    aplicar_fonte(pdf, "Avenir-Regular", 10)
    escrever_texto_seguro(pdf, "As insígnias de especialidade deverão ser colocadas na manga direita da camisa, nos termos estipulados no Regulamento de Uniformes, Distintivos e Bandeiras, e pela ordem apresentada na imagem.", largura_max=90, altura_linha=6, alinhamento="J")
    pdf.ln(4)

    imagem_ordem = baixar_imagem_local(
        "https://especialidades.escutismo.pt/wp-content/uploads/sites/18/2025/02/Especialidades-Ordem-2048x1100.jpg",
        "img_ordem.jpg"
    )
    if imagem_ordem and os.path.exists(imagem_ordem):
        try:
            pdf.image(imagem_ordem, x="C", w=160)
            pdf.ln(6)
        except:
            pass

    
    
    imagem_merito = baixar_imagem_local(
        "https://especialidades.escutismo.pt/wp-content/uploads/sites/18/2022/11/merito.png",
        "img_secao_merito.png"
    )
    imagem_especialista = baixar_imagem_local(
        "https://especialidades.escutismo.pt/wp-content/uploads/sites/18/2022/11/especialista.png",
        "img_secao_especialista.png"
    )

    def escrever_bloco_info(rotulo, texto):
        aplicar_fonte(pdf, "Lilita", 12)
        pdf.cell(0, 7, rotulo, new_x="LMARGIN", new_y="NEXT", align="L")
        aplicar_fonte(pdf, "Avenir-Regular", 10)
        escrever_texto_seguro(pdf, texto, largura_max=90, altura_linha=7, alinhamento="J")
        pdf.ln(4)

    pdf.add_page()
    pdf.set_text_color(*COR_UNICA)
    aplicar_fonte(pdf, "Lilita", 22)
    pdf.cell(0, 12, "Mérito", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    if imagem_merito and os.path.exists(imagem_merito):
        pdf.image(imagem_merito, x="C", w=45)
        pdf.ln(6)

    escrever_bloco_info("OBJETIVO", "Com a presente insígnia pretende-se promover a procura por novos conhecimentos em áreas distintas, contribuindo assim para uma formação mais integral do escuteiro.")
    escrever_bloco_info("DESTINATÁRIOS", "Esta insígnia destina-se a Lobitos, Exploradores, Pioneiros e Caminheiros investidos.")
    escrever_bloco_info("CONDIÇÕES PARA O USO DA INSÍGNIA", "Como condição para o uso da insígnia o escuteiro deverá completar pelo menos uma insígnia de especialidade de 6 áreas distintas.")
    aplicar_fonte(pdf, "Lilita", 12)
    pdf.ln(4)
    pdf.cell(0, 7, "ETAPAS", new_x="LMARGIN", new_y="NEXT", align="L")
    aplicar_fonte(pdf, "Avenir-Regular", 10)
    merit_etapas = [
        "- *Identificar a necessidade*: o elemento deve identificar as áreas e especialidades que se adequam à sua personalidade e interesse, numa perspetiva de validação ou aquisição de novas competências.",
        "- *Negociação*: negociar com a Equipa de Animação as especialidades a adquirir e a forma de operacionalização e validação das provas para a obtenção das mesmas.",
        "- *Conquista*: ir conquistando as especialidades ao longo do tempo em que o escuteiro se encontra na secção, sendo reconhecido pelo trabalho desenvolvido para a obtenção das especialidades.",
        "- *Mérito*: quando o escuteiro atingir os requisitos desta insígnia, a homologação e atribuição da mesma deve ser realizada em Conselho de Guias e entregue em ato solene na secção ou agrupamento."
    ]
    for etapa in merit_etapas:
        escrever_texto_markup_atomic(pdf, etapa, largura_max=90, altura_linha=7)
        pdf.ln(4)

    pdf.add_page()
    pdf.set_text_color(*COR_UNICA)
    aplicar_fonte(pdf, "Lilita", 22)
    pdf.cell(0, 14, "Especialista", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    if imagem_especialista and os.path.exists(imagem_especialista):
        pdf.image(imagem_especialista, x="C", w=45)
        pdf.ln(6)

    escrever_bloco_info("OBJETIVO", "Com a presente insígnia pretende-se reconhecer a especialização e promover a procura por novos conhecimentos numa mesma área, contribuindo assim para uma formação mais integral do escuteiro.")
    escrever_bloco_info("DESTINATÁRIOS", "Esta insígnia destina-se a Lobitos, Exploradores, Pioneiros e Caminheiros investidos.")
    escrever_bloco_info("CONDIÇÕES PARA O USO DA INSÍGNIA", "Como condição para o uso da insígnia o escuteiro deverá completar pelo menos seis insígnias de especialidade do mesmo grupo.")
    aplicar_fonte(pdf, "Lilita", 12)
    pdf.cell(0, 7, "COMO ADQUIRIR A INSÍGNIA", new_x="LMARGIN", new_y="NEXT", align="L")
    aplicar_fonte(pdf, "Avenir-Regular", 10)
    especialista_como_adquirir = [
        "- Adquirir 6 especialidades da mesma área temática.",
        "- No caso dos Pioneiros e Caminheiros, ser tutor de dois escuteiros, ajudando-os a atingir uma especialidade, de preferência, já adquirida pelo tutor.",
        "- A tutoria é validada pelo Conselho de Guias."
    ]
    for item in especialista_como_adquirir:
        escrever_texto_seguro(pdf, item, largura_max=90, altura_linha=7, alinhamento="J")
        pdf.ln(1)

    aplicar_fonte(pdf, "Lilita", 12)
    pdf.cell(0, 7, "ETAPAS", new_x="LMARGIN", new_y="NEXT", align="L")
    aplicar_fonte(pdf, "Avenir-Regular", 10)
    especialista_etapas = [
        "- *Identificação*: identificar as áreas e especialidades que se adequam à sua personalidade e interesse.",
        "- *Negociação*: negociar com a Equipa de Animação as especialidades a adquirir.",
        "- *Tutoria se aplicável*: escolher os tutorandos, planear a tutoria, acompanhar os elementos e articular com a Equipa de Animação ou outros níveis do CNE, sempre com acompanhamento do Conselho de Guias.",
        "- *Validação*: quando o escuteiro atingir os requisitos desta insígnia, a homologação da atribuição da mesma deve ser realizada em Conselho de Guias."
    ]
    for etapa in especialista_etapas:
        escrever_texto_markup_atomic(pdf, etapa, largura_max=90, altura_linha=7)
        pdf.ln(4)

    # ---------------------------------------------------------
    # PARTE: ÍNDICE ALFABÉTICO (UNICA COLUNA, FLUXO CONTÍNUO)
    # ---------------------------------------------------------
    pdf.add_page()
    pdf.set_text_color(*COR_UNICA)
    aplicar_fonte(pdf, "Lilita", 24)
    pdf.cell(0, 15, "Índice Alfabético", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(8)

    aplicar_fonte(pdf, "Avenir-Regular", 11)

    # Preparar entradas (título, página)
    entradas = [(esp["titulo"], mapa_paginas.get(esp["titulo"], "...")) for esp in dados]

    i = 0
    total = len(entradas)
    line_h = 6
    while i < total:
        y = pdf.get_y()
        bottom = pdf.h - pdf.b_margin - 10
        while i < total and (y + line_h) <= bottom:
            titulo, pag = entradas[i]
            pdf.set_xy(15, y)
            aplicar_fonte(pdf, "Avenir-Regular", 11)
            pdf.cell(140, line_h, titulo, align="L")
            pdf.set_xy(15 + 140, y)
            pdf.cell(15, line_h, str(pag), align="R")
            y += line_h
            i += 1
        if i < total:
            pdf.add_page()
            pdf.set_text_color(*COR_UNICA)

    # Guardar os novos números de página
    novo_mapa = {}
    
    # ---------------------------------------------------------
    # PARTE 2: PÁGINAS DE ESPECIALIDADES
    # ---------------------------------------------------------
    for esp in dados:
        pdf.add_page()
        titulo = esp["titulo"]
        novo_mapa[titulo] = pdf.page_no() # Regista a página real
        
        # 1. IMAGEM (Recuperada da cache)
        img_path = IMAGENS_CACHE.get(titulo)
        if img_path and os.path.exists(img_path):
            pdf.image(img_path, x="C", w=40)
            pdf.ln(5)
            
        pdf.set_text_color(*COR_UNICA)
        
        # 2. TÍTULO PRINCIPAL (Lilita)
        aplicar_fonte(pdf, "Lilita", 24)
        escrever_texto_seguro(pdf, titulo, largura_max=60, altura_linha=10, alinhamento="C")
        pdf.ln(12)
        
        # DESCRIÇÃO - Removida conforme pedido!
        
        # 3. ÁREAS
        if esp["areas_formatadas"]:
            aplicar_fonte(pdf, "Lilita", 14)
            pdf.cell(0, 8, "ÁREAS", new_x="LMARGIN", new_y="NEXT", align="L")
            
            aplicar_fonte(pdf, "Avenir-Regular", 12)
            for area in esp["areas_formatadas"]:
                escrever_texto_seguro(pdf, f"- {area}", largura_max=90, altura_linha=7, alinhamento="L")
            pdf.ln(8)
            
        # 4. PROVAS
        aplicar_fonte(pdf, "Lilita", 14)
        pdf.cell(0, 10, "PROVAS", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.ln(2)
        
        for prova in esp.get("provas", []):
            if prova.get("base") or prova.get("avancado"):
                
                # Secção
                aplicar_fonte(pdf, "Avenir-Bold", 12) 
                seccao = limpar_texto(prova.get('seccao', 'Secção'))
                pdf.cell(0, 8, f"{seccao}", new_x="LMARGIN", new_y="NEXT", align="L")
                
                # Base
                if prova.get("base"):
                    aplicar_fonte(pdf, "Avenir-Bold", 11)
                    pdf.cell(0, 6, "Base:", new_x="LMARGIN", new_y="NEXT", align="L")
                    
                    aplicar_fonte(pdf, "Avenir-Regular", 11)
                    for item in prova["base"]:
                        item_txt = limpar_texto(item)
                        escrever_texto_seguro(pdf, f"- {item_txt}", largura_max=90, altura_linha=6, alinhamento="L")
                
                # Avançado
                if prova.get("avancado"):
                    pdf.ln(2)
                    aplicar_fonte(pdf, "Avenir-Bold", 11)
                    pdf.cell(0, 6, "Avançado:", new_x="LMARGIN", new_y="NEXT", align="L")
                    
                    aplicar_fonte(pdf, "Avenir-Regular", 11)
                    for item in prova["avancado"]:
                        item_txt = limpar_texto(item)
                        escrever_texto_seguro(pdf, f"- {item_txt}", largura_max=90, altura_linha=6, alinhamento="L")
                
                pdf.ln(8)

    # ---------------------------------------------------------
    # PARTE: ÍNDICE POR ÁREA (EM 2 COLUNAS) - APÓS ESPECIALIDADES
    # ---------------------------------------------------------
    dicionario_areas = {}
    for esp in dados:
        if not esp["areas_formatadas"]:
            continue
        for area in esp["areas_formatadas"]:
            if area not in dicionario_areas:
                dicionario_areas[area] = []
            dicionario_areas[area].append(esp["titulo"])

    pdf.add_page()
    pdf.set_text_color(*COR_UNICA)
    aplicar_fonte(pdf, "Lilita", 24)
    pdf.cell(0, 15, "Índice por Área", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(8)

    aplicar_fonte(pdf, "Avenir-Regular", 12)

    areas_ordenadas = sorted(dicionario_areas.keys())
    line_h_header = 8
    line_h_item = 5
    spacing = 10  # Espaço entre blocos de áreas
    img_width = 15  # Largura da imagem em mm

    if mapa_imagens_areas is None:
        mapa_imagens_areas = {}

    for area in areas_ordenadas:
        # Verificar espaço; se não houver, nova página
        y = pdf.get_y()
        bottom = pdf.h - pdf.b_margin - 10
        itens = sorted(dicionario_areas[area])
        
        # Calcular altura necessária (imagem + header + items)
        altura_imagem = img_width * 0.75  # Proporção aproximada
        needed = altura_imagem + line_h_header + len(itens) * line_h_item + spacing
        
        if (y + needed) > bottom:
            pdf.add_page()
            pdf.set_text_color(*COR_UNICA)

        # Adicionar imagem + título da área na mesma linha
        y_antes = pdf.get_y()
        img_insertada = False
        
        if area in mapa_imagens_areas:
            img_url = mapa_imagens_areas[area]
            nome_img_area = f"img_area_{area.replace(' ', '_').replace(',', '')}.jpg"
            
            # Baixar imagem se não existir
            if baixar_imagem_local(img_url, nome_img_area):
                try:
                    pdf.image(nome_img_area, x=pdf.l_margin, y=y_antes, w=img_width)
                    img_insertada = True
                except:
                    pass

        aplicar_fonte(pdf, "Avenir-Bold", 11)
        # Se imagem foi inserida, colocar o texto ao lado dela
        if img_insertada:
            pdf.set_xy(pdf.l_margin + img_width + 3, y_antes + (altura_imagem - line_h_header) / 2)
            pdf.cell(0, line_h_header, area, new_x="LMARGIN", new_y="NEXT", align="L")
            pdf.set_y(y_antes + altura_imagem + 5)
        else:
            pdf.cell(0, line_h_header, area, new_x="LMARGIN", new_y="NEXT", align="L")
        
        pdf.ln(3)  # Espaço adicional entre título e items

        aplicar_fonte(pdf, "Avenir-Regular", 10)
        for tit in itens:
            pag = mapa_paginas.get(tit, "...")
            y_item = pdf.get_y()
            if (y_item + line_h_item) > bottom:
                pdf.add_page()
                pdf.set_text_color(*COR_UNICA)
                aplicar_fonte(pdf, "Avenir-Regular", 10)
            pdf.cell(0, line_h_item, f"   - {tit} {' ' * 2}{pag}", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.ln(spacing)


    

    if is_final:
        pdf.output("miolo_temporario.pdf")
        try:
            reader = PdfReader("miolo_temporario.pdf")
            writer = PdfWriter()
            for p in reader.pages:
                writer.add_page(p)
            meta = {
                "/Title": "Sistema de Especialidades",
                "/Author": "Corpo Nacional de Escutas",
                "/Subject": "Especialidades do Corpo Nacional de Escutas",
                "/Keywords": "especialidades, escutismo, CNE",
                "/Creator": "passo5_pdf_estruturado.py",
                "/Producer": "FPDF + pypdf",
                "/CreationDate": datetime.now().strftime("D:%Y%m%d%H%M%S")
            }
            writer.add_metadata(meta)
            with open("miolo_temporario.pdf", "wb") as f_out:
                writer.write(f_out)
        except Exception:
            pass
    return novo_mapa

def gerar_livro_estruturado(guardar_imagens_temporarias=False, section_num=None):
    print("A iniciar compilação do Livro...")
    
    try:
        with open("especialidades.json", "r", encoding="utf-8") as f:
            dados_raw = json.load(f)
    except Exception as e:
        print("Erro ao carregar o JSON:", e)
        return

    print(" -> A processar e formatar as Áreas...")
    dados = []
    for esp in dados_raw:
        esp["titulo"] = limpar_texto(esp.get("titulo", "Sem Título"))
        
        areas_finais = set()
        for area in esp.get("areas", []):
            area_bonita = padronizar_area(area.get("titulo", ""))
            if area_bonita: # Se for None (ex: placeholder), ele ignora
                areas_finais.add(area_bonita)
                
        esp["areas_formatadas"] = sorted(list(areas_finais))
        dados.append(esp)
        
    dados = sorted(dados, key=lambda x: x["titulo"])

    print(" -> A transferir imagens para a cache (Isto só acontece uma vez!)...")
    total = len(dados)
    for i, esp in enumerate(dados, 1):
        titulo = esp["titulo"]
        img_url = esp.get("imagem")
        if img_url:
            nome_img = f"img_cache_{i}.jpg"
            IMAGENS_CACHE[titulo] = nome_img
            if not os.path.exists(nome_img):
                try:
                    r = requests.get(img_url, timeout=10)
                    if r.status_code == 200:
                        with open(nome_img, "wb") as f_img:
                            f_img.write(r.content)
                except:
                    pass

    # Criar mapa de áreas padronizadas para suas imagens (do JSON original)
    mapa_imagens_areas = {}
    for esp in dados_raw:
        for area in esp.get("areas", []):
            area_bonita = padronizar_area(area.get("titulo", ""))
            if area_bonita and area_bonita not in mapa_imagens_areas:
                img_url = area.get("imagem")
                if img_url:
                    mapa_imagens_areas[area_bonita] = img_url

    print(" -> A calcular a paginação exata (Passagem 1/2)...")
    mapa_paginas = compilar_pdf(dados, is_final=False, section_num=section_num, mapa_imagens_areas=mapa_imagens_areas)

    print(" -> A gerar o livro final com os Índices numerados (Passagem 2/2)...")
    compilar_pdf(dados, mapa_paginas=mapa_paginas, is_final=True, section_num=section_num, mapa_imagens_areas=mapa_imagens_areas)

    print(" -> A fundir a capa...")
    # Definir nome do ficheiro final consoante a secção (ou global se None)
    nome_base = "livro_especialidades"
    if section_num is None:
        ficheiro_final = f"{nome_base}.pdf"
    else:
        sufixos = {1: "primeira", 2: "segunda", 3: "terceira", 4: "quarta"}
        ficheiro_final = f"{nome_base}_{sufixos.get(section_num, str(section_num))}.pdf"
    
    if not os.path.exists(CAPA_PATH):
        print("\nATENÇÃO: 'capa.pdf' não encontrado na pasta.")
        print(f"O documento foi gerado apenas com o miolo: miolo_temporario.pdf")
        print(f"Especialidades no livro: {len(dados)}")
        return

    merger = PdfWriter()
    try:
        reader_capa = PdfReader(CAPA_PATH)
        for p in reader_capa.pages: 
            merger.add_page(p)
            
        reader_miolo = PdfReader("miolo_temporario.pdf")
        for p in reader_miolo.pages: 
            merger.add_page(p)
            
        with open(ficheiro_final, "wb") as saida:
            merger.write(saida)

        print(f"\nCOMPLETO! O ficheiro '{ficheiro_final}' está disponível.")
        print(f"Número de especialidades processadas com sucesso: {len(dados)}")
        
    except Exception as e:
        print(f"Erro ao fundir PDFs: {e}")
        
    finally:
        # Fazer as limpezas de ficheiros temporários para a tua pasta ficar limpinha
        if os.path.exists("miolo_temporario.pdf"):
            os.remove("miolo_temporario.pdf")
        if not guardar_imagens_temporarias:
            for ficheiro in ["img_secao_merito.png", "img_secao_especialista.png"]:
                if os.path.exists(ficheiro):
                    os.remove(ficheiro)
            for img in IMAGENS_CACHE.values():
                if os.path.exists(img):
                    os.remove(img)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="Preserva as imagens temporárias para desenvolvimento")
    parser.add_argument("-s", "--section", type=int, choices=[1, 2, 3, 4], help="Exporta apenas especialidades de uma secção (1=Primeira, 2=Segunda, 3=Terceira, 4=Quarta)")
    args = parser.parse_args()
    gerar_livro_estruturado(guardar_imagens_temporarias=args.debug, section_num=args.section)
