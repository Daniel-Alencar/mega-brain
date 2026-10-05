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

## Digital_Down_Conversion: da modulação IQ ao DDC

Animação do conteúdo de
[Digital Down Conversion.md](docs/Detecção%20de%20amplitude%20e%20fase%20em%20RF/Digital%20Down%20Conversion/Digital%20Down%20Conversion.md):

1. **Amplitude e fase → I e Q.** A identidade da soma de arcos transforma
   `A·cos(ωt + φ)` em `I·cos ωt − Q·sin ωt`; as duas ondas somadas e o fasor (I, Q).
2. **Modulação e demodulação IQ.** Diagrama transmissor/receptor.
3. **Demodulação dos canais I e Q.** O produto pelo LO, os termos em 2ωc e o LPF
   que deixa `I(t)/2` e `Q(t)/2`.
4. **Erro de fase Δθ no LO.** Os 4 termos do produto, o que sobrevive ao filtro e
   a projeção num eixo girado: `½·I·cos Δθ − ½·Q·sin Δθ`.
5. **Motivação do DDC.** Nyquist sobre a maior frequência (82 MSps) × sobre a
   largura de banda (2 MSps).
6. **Os três blocos do DDC.** Misturadores digitais, NCO e LPF de decimação.
7. **NCO.** Acumulador de fase, LUT, `f_out = M/2^N · f_CLK`, resolução e
   truncação de fase.
8. **Mistura, filtragem e decimação.** Soma e diferença no espectro e o
   aliasing quando se decima sem filtrar.
9. **Filtro CIC.** Integradores, ↓R e pentes; equivalência com média móvel;
   resposta sinc, droop e crescimento de bits.
10. **DDC × IQ sampling clássico** e resumo.

Cena `DigitalDownConversion` em
[src/Digital_Down_Conversion/digital_down_conversion.py](src/Digital_Down_Conversion/digital_down_conversion.py).
Esta animação **exige LaTeX**.

## IQ_sampling: amplitude e fase com um único ADC

Animação do conteúdo de
[IQ sampling.md](docs/Detecção%20de%20amplitude%20e%20fase%20em%20RF/IQ%20sampling/IQ%20sampling.md):

1. **Polar × cartesiana.** `A·sin(ωt + φ0) = I·sin ωt + Q·cos ωt` e o fasor (I, Q).
2. **O que o ADC mede.** Só a projeção vertical do fasor: uma amostra define uma
   reta; duas amostras a 90° definem o ponto (I, Q).
3. **f_s = 4·f_IF.** O fasor avança 90° por amostra e o ADC entrega Q, I, −Q, −I, …
4. **Algoritmo de rotação.** Janela de 2 amostras e matrizes com 0 e ±1.
5. **Generalização f_s = m·f_IF.** Cada amostra é uma faixa (± ruído); a incerteza
   no cruzamento cresce com `1/|sin Δφ|`.
6. **Limitações.** Offset DC gera ripple em f_IF; com f_s = 4·f_IF, as harmônicas
   ímpares caem sobre a portadora (no espectro e no tempo).
7. **Resumo.**

Cena `IQSampling` em [src/IQ_sampling/iq_sampling.py](src/IQ_sampling/iq_sampling.py).
Esta animação **exige LaTeX**.

## Non_IQ_sampling: N amostras em M períodos

Animação do conteúdo de
[Non-IQ sampling.md](docs/Detecção%20de%20amplitude%20e%20fase%20em%20RF/Non-IQ%20sampling/Non-IQ%20sampling.md),
com o exemplo N = 9, M = 2 (f_s = 4,5·f_IF, Δφ = 80°):

1. **Motivação.** Harmônicas ímpares sobre f_IF no IQ sampling.
2. **Conceito.** `f_s/f_IF = N/M` e N pontos distintos no círculo.
3. **Mínimos quadrados.** Amostras com ruído, resíduos e a função de custo
   diminuindo até o mínimo.
4. **Por que fica simples.** A soma dos vetores `e^{j2φi}` fecha um polígono, então
   `p12 = 0` e `p11 = p22 = N/2`.
5. **Estimador final.** `I = (2/N)·Σ y·sin(iΔφ)`, `Q = (2/N)·Σ y·cos(iΔφ)` com
   coeficientes de uma LUT.
6. **Harmônicas espalhadas.** Com f_s = 4,5·f_IF nenhuma das 7 primeiras cai sobre
   f_IF; as primeiras a cair são a (N−1)ª e a (N+1)ª.
7. **Ruído e offset.** Nuvens de estimativas IQ × Non-IQ; o offset DC se cancela.
8. **Latência.** Uma estimativa por amostra × uma a cada N amostras.
9. **Resumo** em tabela.

Cena `NonIQSampling` em
[src/Non_IQ_sampling/non_iq_sampling.py](src/Non_IQ_sampling/non_iq_sampling.py).
Esta animação **exige LaTeX**.

## Filtros: ordem, roll-off, ressonância e o RLC

Animação do conteúdo de [Filtros.md](docs/Filtros/Filtros.md):

1. **Ordem.** Grau de D(s) = nº de polos = nº de elementos reativos (RC × RLC).
2. **Roll-off.** Bode de 1ª ordem (−20 dB/década) × 2ª ordem (−40 dB/década).
3. **Comportamento dinâmico.** Polos no plano s e resposta ao degrau variando ζ (e Q).
4. **1ª ordem.** RC série: tensão no C (passa-baixa) e no R (passa-alta), com varredura de ω.
5. **2ª ordem.** Mesmo D(s); o numerador define LP, BP ou HP; efeito de Q. Tabela-resumo.
6. **RLC série, quatro filtros.** V_C, V_L, V_R e V_LC ⇒ LP, HP, BP e notch.
7. **Série × paralelo.** |Z| mínima × máxima em ω₀ e a divisão de corrente nos ramos.

Cena `Filtros` em [src/Filtros/filtros.py](src/Filtros/filtros.py). Exige LaTeX.

## Modelagem_cavidade_RF: do campo 3D ao passa-banda

Animação do conteúdo de
[Modelagem de uma cavidade de RF.md](docs/Modelagem%20de%20uma%20cavidade%20de%20RF/Modelagem%20de%20uma%20cavidade%20de%20RF.md):

1. **Por que RLC paralelo.** Campo E axial ↔ C, campo B azimutal ↔ L, perdas nas paredes ↔ R,
   com a energia oscilando entre W_E e W_M.
2. **Circuito equivalente.** Gerador (Norton), acoplador 1:n, cavidade e feixe em pacotes.
3. **Rebatimento.** V₂ = nV₁, I₂ = I₁/n ⇒ Z₀' = n²Z₀; o transformador desaparece.
4. **Lei dos nós.** Correntes nos ramos e a equação diferencial de 2ª ordem.
5. **Laplace.** A impedância V_C(s)/I_C(s).
6. **Forma canônica.** ω₀ = 1/√(LC), 2ω½ e K = 1/C.
7. **Resposta em frequência.** L em curto, C em curto e L∥C aberto em ω₀.

Cena `ModelagemCavidade` em
[src/Modelagem_cavidade_RF/modelagem_cavidade.py](src/Modelagem_cavidade_RF/modelagem_cavidade.py). Exige LaTeX.

## Componentes_sistema_RF: a malha LLRF

Animação do conteúdo de
[Componentes de um sistema de RF.md](docs/Componentes%20de%20um%20sistema%20de%20RF/Componentes%20de%20um%20sistema%20de%20RF.md):

1. **A malha completa.** FPGA → DAC → mixer → filtro → amplificador → linhas → cavidade →
   atenuadores → mixer → filtro → ADC → FPGA, com os 7 componentes numerados.
2. **LLRF.** O PI corrige perturbações e mantém o fasor na faixa de tolerância.
3. **Conversores.** Quantização do ADC e reconstrução em escada do DAC.
4. **Down-conversion.** Produto de cossenos e espectro (20 e 980 MHz) com o passa-baixa.
5. **Por que 20 MHz.** Jitter (Δv ≈ dv/dt·Δt), 5 amostras por período, offset DC e ruído 1/f.
6. **Up-conversion.** 500 e 460 MHz, vazamento do LO e o passa-banda.
7. **Por que 500 MHz.** Ressonância da cavidade e pacotes na crista do campo.
8. **IQ na FPGA.** Desmodulação após o ADC e modulação (NCO) antes do DAC.
9. **Cadeia de potência.** PreAmp, SSAMP, fontes e guias de onda.
10. **Banda × ripple.** Sensibilidade |S| para BW de 1 kHz e 50 kHz com ripple de 10 kHz.

Cena `ComponentesSistemaRF` em
[src/Componentes_sistema_RF/componentes_sistema_rf.py](src/Componentes_sistema_RF/componentes_sistema_rf.py).
Exige LaTeX.

## Estrutura

```
Master-Brain/
├── src/
│   ├── IQ_modulation/
│   │   ├── iq_manim_llrf.py      # analógico × digital (DDC)
│   │   └── amplitude_fase_iq.py  # como extrair amplitude e fase de I/Q
│   ├── Digital_Down_Conversion/
│   │   └── digital_down_conversion.py  # modulação IQ, NCO, CIC e DDC
│   ├── IQ_sampling/
│   │   └── iq_sampling.py              # f_s = 4·f_IF e algoritmo de rotação
│   ├── Non_IQ_sampling/
│   │   └── non_iq_sampling.py          # f_s/f_IF = N/M e mínimos quadrados
│   ├── Filtros/
│   │   └── filtros.py                  # ordem, roll-off, ressonância, RLC
│   ├── Modelagem_cavidade_RF/
│   │   └── modelagem_cavidade.py       # cavidade → RLC paralelo → passa-banda
│   └── Componentes_sistema_RF/
│       └── componentes_sistema_rf.py   # malha LLRF completa
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

```bash
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libglib-2.0.so.0 \
    manim -pql src/Digital_Down_Conversion/digital_down_conversion.py DigitalDownConversion
```

```bash
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libglib-2.0.so.0 \
    manim -pql src/IQ_sampling/iq_sampling.py IQSampling
```

```bash
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libglib-2.0.so.0 \
    manim -pql src/Non_IQ_sampling/non_iq_sampling.py NonIQSampling
```

```bash
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libglib-2.0.so.0 manim -pql src/Filtros/filtros.py Filtros
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libglib-2.0.so.0 manim -pql src/Modelagem_cavidade_RF/modelagem_cavidade.py ModelagemCavidade
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libglib-2.0.so.0 manim -pql src/Componentes_sistema_RF/componentes_sistema_rf.py ComponentesSistemaRF
```

O `-p` abre o vídeo assim que ele termina de renderizar. Os arquivos ficam em:

```
media/videos/iq_manim_llrf/480p15/IQDemodulationComparison.mp4
media/videos/amplitude_fase_iq/480p15/AmplitudeFaseIQ.mp4
media/videos/digital_down_conversion/480p15/DigitalDownConversion.mp4
media/videos/iq_sampling/480p15/IQSampling.mp4
media/videos/non_iq_sampling/480p15/NonIQSampling.mp4
media/videos/filtros/480p15/Filtros.mp4
media/videos/modelagem_cavidade/480p15/ModelagemCavidade.mp4
media/videos/componentes_sistema_rf/480p15/ComponentesSistemaRF.mp4
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
