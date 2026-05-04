# Escutismo Especialidades

Gera automaticamente o livro de especialidades do Escutismo em PDF a partir dos dados extraídos do site oficial.

## O que faz

- Atualiza o ficheiro `especialidades.json` com os dados mais recentes.
- Gera PDFs por secção e o livro completo.
- Usa a capa e as fontes guardadas em `assets/`.
- Publica os PDFs numa release do GitHub apenas quando houver diferenças face à release anterior.

## Estrutura principal

- `atualizar_especialidades.py` - recolhe e grava os dados em `especialidades.json`.
- `gerar_pdf.py` - gera os PDFs.
- `assets/capa.pdf` - capa do livro.
- `assets/fonts/` - fontes usadas na geração.
- `.github/workflows/gerar_pdf.yml` - workflow manual do GitHub Actions.

## Requisitos

- Python 3.11 ou superior.
- Ligação à internet para recolher os dados e imagens.

## Instalação local

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Como gerar os ficheiros localmente

1. Atualizar os dados:

```bash
python atualizar_especialidades.py
```

2. Gerar os PDFs das 4 secções e o livro completo:

```bash
python gerar_pdf.py -d -s 1
python gerar_pdf.py -d -s 2
python gerar_pdf.py -d -s 3
python gerar_pdf.py -d -s 4
python gerar_pdf.py
```

## Ficheiros gerados

O script cria estes PDFs:

- `livro_especialidades_primeira.pdf`
- `livro_especialidades_segunda.pdf`
- `livro_especialidades_terceira.pdf`
- `livro_especialidades_quarta.pdf`
- `livro_especialidades.pdf`

## GitHub Actions

O workflow em `.github/workflows/gerar_pdf.yml` não corre em `push`.

Para gerar os ficheiros no GitHub, tens de ir a Actions e clicar manualmente em **Run workflow**.

O processo faz isto:

1. Atualiza as especialidades.
2. Gera os 5 PDFs.
3. Compara os PDFs com a última release.
4. Se houver diferenças, cria uma nova release e anexa os PDFs.
5. Se não houver diferenças, não cria release nova.

## Limpeza de ficheiros temporários

O repositório inclui um `.gitignore` para evitar subir ficheiros temporários, caches de imagens e PDFs gerados localmente.

## Notas

- A geração depende da estrutura atual do site do Escutismo.
- Se o site mudar, pode ser necessário ajustar o scraper em `atualizar_especialidades.py`.
- As imagens e a capa usadas no livro pertencem aos respetivos autores e entidades.