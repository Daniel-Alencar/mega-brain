# Master-Brain

Animações e simulações didáticas de processamento de sinais para sistemas LLRF
de aceleradores de partículas.

## IQ_modulation: detecção I/Q analógica × digital (DDC)

Animação em [Manim Community](https://www.manim.community/) que compara as duas
formas de medir I e Q do campo de uma cavidade de RF:

1. **Fasor e decomposição I/Q.** Um fasor girante e suas projeções
   `I = A·cos φ` e `Q = A·sin φ`, com a trajetória em espiral e depois em círculo.
2. **Desmodulação analógica direta (Fig. 5b).** O diagrama de blocos com dois
   canais de cobre, o híbrido a 95° em vez de 90° (erro Δθ) e o ganho `(1+ε)` no
   canal Q. No plano complexo, o círculo vira uma elipse inclinada, e o termo de
   diafonia `−½·Q·sin Δθ` aparece em destaque.
3. **IF + ADC + DDC (Fig. 5c).** Um único mixer leva a portadora para 20 MHz e
   um único ADC amostra a 80 MSPS (`f_s = 4·f_IF`, amostras I, −Q, −I, +Q).
   Dentro da FPGA, os eixos I/Q gerados numericamente ficam a 90,000° e a
   trajetória recuperada é um círculo perfeito.
4. **Resumo.** Os dois métodos lado a lado.

A animação inteira está numa única cena, `IQDemodulationComparison`, em
[src/IQ_modulation/iq_manim_llrf.py](src/IQ_modulation/iq_manim_llrf.py).

## IQ_modulation: como medir amplitude e fase com I/Q

Animação que mostra como sair de I/Q para amplitude e fase. Ela parte da
demodulação descrita em [Modulação IQ.md](Modulação%20IQ.md):

1. **O que são amplitude e fase.** A é a altura da onda; φ é o adiantamento em
   relação ao LO (φ = ω·Δt).
2. **O truque do LO.** Girar junto com o LO "congela" o fasor do RF. Demodular
   é multiplicar por `e^{−jωt}`: a parte real é o mixer I e a imaginária, o mixer Q.
3. **Por que um mixer só não basta.** Ele mede uma única projeção, `½·A·cos φ`,
   e infinitos pares (A, φ) dão a mesma saída. Um segundo mixer com o LO
   deslocado de 90° mede a outra projeção e resolve a ambiguidade.
4. **De (I, Q) para (A, φ).** `A = √(I² + Q²)` e `φ = atan2(Q, I)`, mostrando
   por que `arctan(Q/I)` erra o quadrante.
5. **A(t) e φ(t) em tempo real.** Enchimento da cavidade seguido de um salto de fase.
6. **Os três esquemas da Fig. 5 (Schilcher).** Detector de amplitude e fase,
   I/Q analógico e I/Q digital (DDC).

Cena `AmplitudeFaseIQ` em
[src/IQ_modulation/amplitude_fase_iq.py](src/IQ_modulation/amplitude_fase_iq.py).
Esta animação **exige LaTeX**, porque usa `MathTex` e `DecimalNumber`.

## Estrutura

```
Master-Brain/
├── src/
│   └── IQ_modulation/
│       ├── iq_manim_llrf.py      # analógico × digital (DDC)
│       └── amplitude_fase_iq.py  # como extrair amplitude e fase de I/Q
├── media/
└── venv/
```

## Requisitos

Testado no Ubuntu 24.04 com Python 3.12 e Manim 0.21.0.

### Pacotes do sistema

```bash
# Bibliotecas usadas pelo Manim para desenhar e renderizar texto
sudo apt install build-essential python3-dev pkg-config libcairo2-dev libpango1.0-dev ffmpeg

# LaTeX para as fórmulas (MathTex)
sudo apt install texlive texlive-latex-extra dvisvgm
```

Em `iq_manim_llrf.py` o LaTeX é **opcional**. A cena verifica se `latex` e
`dvisvgm` estão no PATH: se estiverem, as fórmulas usam `MathTex`; se não, viram
texto Unicode e a animação renderiza do mesmo jeito. Já `amplitude_fase_iq.py`
precisa de LaTeX.

### Ambiente Python

Na raiz do repositório:

```bash
python3 -m venv venv
source venv/bin/activate
pip install manim
```

## Executar

Com o venv ativado, a partir da raiz do repositório:

```bash
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libglib-2.0.so.0 \
    manim -pql src/IQ_modulation/iq_manim_llrf.py IQDemodulationComparison
```

```bash
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libglib-2.0.so.0 \
    manim -pql src/IQ_modulation/amplitude_fase_iq.py AmplitudeFaseIQ
```

O `-p` abre o vídeo assim que ele termina de renderizar. Os arquivos ficam em:

```
media/videos/iq_manim_llrf/480p15/IQDemodulationComparison.mp4
media/videos/amplitude_fase_iq/480p15/AmplitudeFaseIQ.mp4
```

Para que serve o `LD_PRELOAD`, veja [Problemas comuns](#problemas-comuns).

### Qualidade de renderização

| Flag  | Resolução | Uso                                  |
|-------|-----------|--------------------------------------|
| `-ql` | 480p15    | rascunho rápido                      |
| `-qm` | 720p30    | revisão                              |
| `-qh` | 1080p60   | versão final                         |
| `-qk` | 2160p60   | 4K                                   |

Outras opções úteis:

```bash
# Renderiza só o último quadro como PNG (bom para checar o layout)
manim -sql src/IQ_modulation/iq_manim_llrf.py IQDemodulationComparison

# Exporta como GIF
manim -ql --format gif src/IQ_modulation/iq_manim_llrf.py IQDemodulationComparison
```

As mesmas regras do `LD_PRELOAD` valem para esses comandos.

## Personalização

No topo de `iq_manim_llrf.py`:

| Constante                         | Padrão         | O que controla                                        |
|-----------------------------------|----------------|-------------------------------------------------------|
| `DTH_EXAGERADO`                   | `20.0`         | erro de quadratura Δθ (graus) usado para mostrar a elipse |
| `EPS_EXAGERADO`                   | `0.30`         | desbalanço de ganho ε usado para mostrar a elipse      |
| `COR_REAL`, `COR_I`, `COR_Q`, ... | azul, dourado, verde, ... | paleta: real, canal I, canal Q, distorções   |
| `FUNDO`                           | `#0e1117`      | cor de fundo                                          |

A Cena 2 mostra primeiro o erro realista (Δθ = 5°, ou seja, 95°) e depois aplica
os valores exagerados, porque 5° quase não deforma o círculo a olho nu.

## Problemas comuns

**`undefined symbol` em `libglib`/`libpango`, ou erro ao importar `manimpango`.**
É por isso que o `LD_PRELOAD` está no comando. A causa provável é que o venv foi
criado com o Python do Anaconda, que traz uma `libglib` mais antiga do que a que
o Pango do sistema exige. O `LD_PRELOAD` obriga o processo a carregar a glib do
sistema. Outra saída é criar o venv com o Python do sistema, que dispensa o
`LD_PRELOAD`:

```bash
sudo apt install python3-venv
/usr/bin/python3 -m venv venv
source venv/bin/activate
pip install manim
```

**`pip install manim` falha ao compilar `manimpango` ou `pycairo`.**
Faltam os cabeçalhos de desenvolvimento. Instale
`libcairo2-dev libpango1.0-dev pkg-config python3-dev`.

**Erro de LaTeX ao renderizar (`LaTeX Error: File '...sty' not found`).**
Falta algum pacote LaTeX. Instale `texlive-latex-extra`, ou `texlive-full`
para ter todos. Outra opção é desinstalar o LaTeX, e a cena passa a usar texto
Unicode.
