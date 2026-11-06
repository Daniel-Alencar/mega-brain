#!/usr/bin/env bash
#
# Renderiza as animações do repositório pelo nome da cena, sem precisar digitar
# o caminho do arquivo (que tem espaços, acentos e prefixos numéricos).
#
#     ./render.sh DigitalDownConversion      rascunho 480p, abre ao terminar
#     ./render.sh filtro_cic -q h            final 1080p
#     ./render.sh --lista                    mostra todas as cenas
#     ./render.sh --todas -n                 renderiza tudo, sem abrir
#
# O Makefile na raiz é um atalho para isto: `make DigitalDownConversion`.
#
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$RAIZ"

QUALIDADE="${Q:-l}"       # l=480p15  m=720p30  h=1080p60  k=4K
PREVIA="${P:-1}"          # 1 abre o vídeo ao terminar; 0 não
EXTRA=()                  # argumentos repassados ao manim

# -----------------------------------------------------------------------------
# Ambiente
# -----------------------------------------------------------------------------
MANIM=()

# Descobre como chamar o manim, na primeira vez que for preciso.
#
# Testar se o arquivo existe não basta. Os scripts de um venv guardam o caminho
# absoluto do interpretador na primeira linha, e esse caminho quebra se a pasta
# do projeto for renomeada; e um venv pode ter o pacote instalado mas um
# interpretador inconsistente. Por isso cada candidato é testado de verdade,
# com --version, e usamos o primeiro que responder.
achar_manim() {
    [[ ${#MANIM[@]} -gt 0 ]] && return 0
    local tentativa
    local -a cmd
    for tentativa in venv path sistema; do
        case $tentativa in
            venv)    [[ -x venv/bin/python ]] || continue
                     cmd=("$RAIZ/venv/bin/python" -m manim) ;;
            path)    command -v manim >/dev/null 2>&1 || continue
                     cmd=("$(command -v manim)") ;;
            sistema) cmd=(python3 -m manim) ;;
        esac
        if "${cmd[@]}" --version >/dev/null 2>&1; then
            MANIM=("${cmd[@]}")
            return 0
        fi
    done
    echo "erro: nenhum manim utilizável encontrado. Instale com:" >&2
    echo "      python3 -m venv venv && venv/bin/pip install manim" >&2
    exit 1
}

# Contorna o conflito de bibliotecas entre o Cairo do sistema e o do venv.
GLIB=/usr/lib/x86_64-linux-gnu/libglib-2.0.so.0
[[ -e $GLIB ]] && export LD_PRELOAD="${LD_PRELOAD:-}${LD_PRELOAD:+:}$GLIB"

# -----------------------------------------------------------------------------
# Índice das cenas: "NomeDaCena<TAB>arquivo.py" em ordem de estudo
# -----------------------------------------------------------------------------
indice() {
    # Ordena pelo diretório, não pelo caminho inteiro: como o diretório de um
    # assunto é prefixo do das subpastas dele, o .py do assunto vem primeiro
    # (digital_down_conversion.py antes de "1 - Decimador/decimador.py").
    # -V trata os prefixos numéricos como números, então 10 virá depois de 9.
    find src -name '*.py' \
        | while IFS= read -r a; do
            printf '%s\t%s\t%s\n' "$(dirname "$a")" "$(basename "$a")" "$a"
        done \
        | LC_ALL=C sort -t$'\t' -k1,1V -k2,2V \
        | cut -f3- \
        | while IFS= read -r arquivo; do
            sed -n 's/^class \([A-Za-z_][A-Za-z0-9_]*\)(Scene).*/\1/p' "$arquivo" \
                | while read -r cena; do
                    printf '%s\t%s\n' "$cena" "$arquivo"
                done
        done
}

# Nomes aceitos como alvo: a cena e o nome do arquivo sem extensão.
nomes() {
    indice | while IFS=$'\t' read -r cena arquivo; do
        printf '%s\n%s\n' "$cena" "$(basename "$arquivo" .py)"
    done
}

lista() {
    printf '\n  \033[1mCenas disponíveis\033[0m (na ordem de estudo)\n\n'
    indice | while IFS=$'\t' read -r cena arquivo; do
        assunto="$(dirname "${arquivo#src/}")"
        printf '  \033[36m%-28s\033[0m %s\n' "$cena" "$assunto"
    done
    printf '\n  Renderize com:  make <Cena>   ou   ./render.sh <Cena>\n\n'
}

# Resolve um apelido (cena, nome de arquivo ou caminho) para "cena<TAB>arquivo".
resolver() {
    local alvo="$1" achado
    achado="$(indice | awk -F'\t' -v a="$alvo" '
        tolower($1) == tolower(a) { print; exit }')"
    [[ -n $achado ]] && { printf '%s\n' "$achado"; return 0; }

    achado="$(indice | awk -F'\t' -v a="$alvo" '
        { n = $2; sub(/.*\//, "", n); sub(/\.py$/, "", n) }
        tolower(n) == tolower(a) { print; exit }')"
    [[ -n $achado ]] && { printf '%s\n' "$achado"; return 0; }

    achado="$(indice | awk -F'\t' -v a="${alvo%.py}" '
        index($2, a) && a != "" { print; exit }')"
    [[ -n $achado ]] && { printf '%s\n' "$achado"; return 0; }

    return 1
}

renderizar() {
    local cena="$1" arquivo="$2"
    achar_manim
    local args=(-q "$QUALIDADE" --disable_caching)
    [[ $PREVIA == 1 ]] && args+=(-p)
    [[ ${#EXTRA[@]} -gt 0 ]] && args+=("${EXTRA[@]}")

    printf '\n\033[1m→ %s\033[0m  (%s)\n' "$cena" "$arquivo"
    "${MANIM[@]}" "${args[@]}" "$arquivo" "$cena"

    local saida
    saida="$(find media/videos/"$(basename "$arquivo" .py)" -name "$cena.mp4" \
             -newermt '-10 minutes' 2>/dev/null | head -1)"
    [[ -n $saida ]] && printf '\033[32m✓ %s\033[0m\n' "$saida"
}

ajuda() {
    # imprime o cabeçalho do próprio arquivo, até a primeira linha que não é comentário
    awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "${BASH_SOURCE[0]}"
    printf 'Opções:\n'
    printf '  -q l|m|h|k      qualidade: 480p15, 720p30, 1080p60, 4K (padrão: l)\n'
    printf '  -n              não abrir o vídeo ao terminar\n'
    printf '  --lista         lista as cenas e sai\n'
    printf '  --todas         renderiza todas as cenas\n'
    printf '  --onde <nome>   mostra a que arquivo e cena um nome resolve\n'
    printf '  --ambiente      mostra qual manim será usado\n'
    printf '  --              o que vier depois vai direto para o manim\n\n'
}

# -----------------------------------------------------------------------------
# Argumentos
# -----------------------------------------------------------------------------
ALVOS=()
TODAS=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help|--ajuda) ajuda; exit 0 ;;
        -l|--lista|--list) lista; exit 0 ;;
        --nomes)           nomes; exit 0 ;;
        --ambiente)        # mostra qual manim será usado, útil quando algo quebra
            achar_manim
            printf 'manim:      %s\n' "${MANIM[*]}"
            printf 'versão:     %s\n' "$("${MANIM[@]}" --version 2>&1 | head -1)"
            printf 'LD_PRELOAD: %s\n' "${LD_PRELOAD:-(nenhum)}"
            exit 0 ;;
        --onde)            # mostra o que um apelido resolve, sem renderizar
            if achado="$(resolver "$2")"; then
                IFS=$'\t' read -r c a <<<"$achado"
                printf '%s\n  %s\n' "$c" "$a"; exit 0
            fi
            echo "erro: cena '$2' não encontrada" >&2; exit 1 ;;
        -a|--todas|--all)  TODAS=1; shift ;;
        -n|--sem-previa)   PREVIA=0; shift ;;
        -q|--qualidade)    QUALIDADE="$2"; shift 2 ;;
        -q*)               QUALIDADE="${1#-q}"; shift ;;
        --)                shift; EXTRA+=("$@"); break ;;
        -*)                EXTRA+=("$1"); shift ;;
        *)                 ALVOS+=("$1"); shift ;;
    esac
done

case "$QUALIDADE" in
    l|m|h|k) ;;
    *) echo "erro: qualidade '$QUALIDADE' inválida (use l, m, h ou k)" >&2; exit 1 ;;
esac

if [[ $TODAS == 1 ]]; then
    while IFS=$'\t' read -r cena arquivo; do
        renderizar "$cena" "$arquivo"
    done < <(indice)
    exit 0
fi

if [[ ${#ALVOS[@]} -eq 0 ]]; then
    lista
    exit 0
fi

for alvo in "${ALVOS[@]}"; do
    if achado="$(resolver "$alvo")"; then
        IFS=$'\t' read -r cena arquivo <<<"$achado"
        renderizar "$cena" "$arquivo"
    else
        echo "erro: cena '$alvo' não encontrada. Veja as disponíveis com --lista" >&2
        exit 1
    fi
done
