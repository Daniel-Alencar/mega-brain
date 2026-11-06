# Atalhos para renderizar as animações.
#
#   make                            lista as cenas disponíveis
#   make DigitalDownConversion      rascunho 480p, abre o vídeo ao terminar
#   make FiltroCIC Q=h              versão final, 1080p
#   make AmostragemAliasing P=0     não abre o vídeo ao terminar
#   make todas                      renderiza tudo
#   make limpar                     apaga os vídeos gerados
#
# O trabalho de verdade está em render.sh — este arquivo só expõe um alvo com o
# nome de cada cena, para que `make <TAB>` complete os nomes. Os caminhos dos
# .py têm espaços e acentos, que o make não trata bem; por isso eles nunca
# aparecem aqui: quem resolve o nome da cena para um caminho é o script.

SHELL := /bin/bash
RENDER := bash render.sh
CENAS := $(shell $(RENDER) --nomes)

export Q
export P

.DEFAULT_GOAL := ajuda
.PHONY: ajuda help lista list todas all limpar clean $(CENAS)

ajuda:
	@$(RENDER) --lista
	@echo "  Qualidade:  Q=l (480p, padrão)  Q=m (720p)  Q=h (1080p)  Q=k (4K)"
	@echo "  Sem abrir:  P=0"
	@echo "  Tudo:       make todas          Limpar: make limpar"
	@echo

lista:
	@$(RENDER) --lista

todas:
	@$(RENDER) --todas

$(CENAS):
	@$(RENDER) $@

limpar:
	@rm -rf media/videos media/images media/texts media/Tex
	@echo "removido: media/ (vídeos, imagens e intermediários do LaTeX)"

# Aliases em inglês, pela convenção
help: ajuda
list: lista
all: todas
clean: limpar
