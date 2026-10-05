# Mega-Brain

Conteúdo e animações didáticas de processamento de sinais para sistemas LLRF
(*Low Level RF*) de aceleradores de partículas.

O repositório tem duas partes que andam juntas:

- **`docs/`**: um texto em Markdown para cada assunto, independente e completo.
- **`src/`**: uma animação em [Manim Community](https://www.manim.community/) para
  cada texto, na pasta de mesmo nome.

## Assuntos

| Assunto | Texto | Animação | Cena | Duração |
|---|---|---|---|---|
| Componentes de um sistema de RF | [.md](docs/Componentes%20de%20um%20sistema%20de%20RF/Componentes%20de%20um%20sistema%20de%20RF.md) | [componentes_sistema_rf.py](src/Componentes%20de%20um%20sistema%20de%20RF/componentes_sistema_rf.py) | `ComponentesSistemaRF` | ~4 min |
| Modelagem de uma cavidade de RF | [.md](docs/Modelagem%20de%20uma%20cavidade%20de%20RF/Modelagem%20de%20uma%20cavidade%20de%20RF.md) | [modelagem_cavidade.py](src/Modelagem%20de%20uma%20cavidade%20de%20RF/modelagem_cavidade.py) | `ModelagemCavidade` | ~3 min |
| Filtros | [.md](docs/Filtros/Filtros.md) | [filtros.py](src/Filtros/filtros.py) | `Filtros` | ~3 min |
| Detecção de amplitude e fase: IQ sampling | [.md](docs/Detecção%20de%20amplitude%20e%20fase%20em%20RF/IQ%20sampling/IQ%20sampling.md) | [iq_sampling.py](src/Detecção%20de%20amplitude%20e%20fase%20em%20RF/IQ%20sampling/iq_sampling.py) | `IQSampling` | ~3 min |
| Detecção de amplitude e fase: Non-IQ sampling | [.md](docs/Detecção%20de%20amplitude%20e%20fase%20em%20RF/Non-IQ%20sampling/Non-IQ%20sampling.md) | [non_iq_sampling.py](src/Detecção%20de%20amplitude%20e%20fase%20em%20RF/Non-IQ%20sampling/non_iq_sampling.py) | `NonIQSampling` | ~3 min |
| Detecção de amplitude e fase: Digital Down Conversion | [.md](docs/Detecção%20de%20amplitude%20e%20fase%20em%20RF/Digital%20Down%20Conversion/Digital%20Down%20Conversion.md) | [digital_down_conversion.py](src/Detecção%20de%20amplitude%20e%20fase%20em%20RF/Digital%20Down%20Conversion/digital_down_conversion.py) | `DigitalDownConversion` | ~6 min |

Uma ordem natural de estudo é a da tabela: primeiro a malha LLRF como um todo,
depois a cavidade e os filtros, e por fim as três técnicas de detecção de
amplitude e fase.

## O que cada animação mostra

### Componentes de um sistema de RF

1. **A malha completa.** FPGA → DAC → mixer → filtro → amplificador → linhas →
   cavidade → atenuadores → mixer → filtro → ADC → FPGA, com os 7 componentes numerados.
2. **LLRF.** O PI corrige perturbações e mantém o fasor do campo na faixa de tolerância.
3. **Conversores.** Quantização do ADC e reconstrução em escada do DAC.
4. **Down-conversion.** Produto de cossenos e espectro (20 e 980 MHz) com o passa-baixa.
5. **Por que 20 MHz.** Jitter (`Δv ≈ dv/dt·Δt`), 5 amostras por período, offset DC e ruído 1/f.
6. **Up-conversion.** 500 e 460 MHz, vazamento do LO e o passa-banda.
7. **Por que 500 MHz.** Ressonância da cavidade e pacotes chegando na crista do campo.
8. **IQ na FPGA.** Desmodulação logo após o ADC e modulação (NCO) logo antes do DAC.
9. **Cadeia de potência.** PreAmp, SSAMP, fontes de alimentação e guias de onda.
10. **Banda × ripple.** Função de sensibilidade |S| para BW de 1 kHz e 50 kHz com
    ripple de 10 kHz (modelo simples `C(s)H(s) ≈ ω_BW/s`).

### Modelagem de uma cavidade de RF

1. **Por que RLC paralelo.** Campo E axial ↔ C, campo B azimutal ↔ L, perdas nas
   paredes ↔ R, com a energia oscilando entre W_E e W_M.
2. **Circuito equivalente.** Gerador de Norton (`I'rf ∥ Z₀`), acoplador 1:n,
   cavidade e o feixe passando em pacotes.
3. **Rebatimento.** `V₂ = n·V₁`, `I₂ = I₁/n` ⇒ `Z₀' = n²·Z₀`; o transformador desaparece.
4. **Lei dos nós.** Correntes nos ramos até a equação diferencial de 2ª ordem.
5. **Laplace.** A impedância `V_C(s)/I_C(s)`.
6. **Forma canônica.** `ω₀ = 1/√(LC)`, `2ω½` e `K = 1/C`.
7. **Resposta em frequência.** L em curto, C em curto e L∥C aberto em ω₀.

### Filtros

1. **Ordem.** Grau de D(s) = nº de polos = nº de elementos reativos (RC × RLC).
2. **Roll-off.** Bode de 1ª ordem (−20 dB/década) × 2ª ordem (−40 dB/década).
3. **Comportamento dinâmico.** Polos no plano s e resposta ao degrau variando ζ (e Q).
4. **1ª ordem.** RC série: tensão no C (passa-baixa) e no R (passa-alta), com varredura de ω.
5. **2ª ordem.** Mesmo D(s); o numerador define LP, BP ou HP; efeito de Q; tabela-resumo.
6. **RLC série, quatro filtros.** V_C, V_L, V_R e V_LC ⇒ LP, HP, BP e notch.
7. **Série × paralelo.** |Z| mínima × máxima em ω₀ e a divisão de corrente nos ramos.

### IQ sampling

1. **Polar × cartesiana.** `A·sin(ωt + φ0) = I·sin ωt + Q·cos ωt` e o fasor (I, Q).
2. **O que o ADC mede.** Só a projeção vertical do fasor: uma amostra define uma
   reta; duas amostras a 90° definem o ponto (I, Q).
3. **f_s = 4·f_IF.** O fasor avança 90° por amostra e o ADC entrega Q, I, −Q, −I, …
4. **Algoritmo de rotação.** Janela de 2 amostras e matrizes só com 0 e ±1.
5. **Generalização f_s = m·f_IF.** Cada amostra é uma faixa (± ruído); a incerteza
   no cruzamento cresce com `1/|sin Δφ|`.
6. **Limitações.** Offset DC gera ripple em f_IF; com f_s = 4·f_IF as harmônicas
   ímpares caem sobre a portadora (no espectro e no tempo).
7. **Resumo.**

### Non-IQ sampling

Exemplo usado: N = 9, M = 2 (f_s = 4,5·f_IF, Δφ = 80°).

1. **Motivação.** Harmônicas ímpares sobre f_IF no IQ sampling.
2. **Conceito.** `f_s/f_IF = N/M` e N pontos distintos no círculo.
3. **Mínimos quadrados.** Amostras com ruído, resíduos e a função de custo
   diminuindo até o mínimo.
4. **Por que fica simples.** A soma dos vetores `e^{j2φi}` fecha um polígono, então
   `p12 = 0` e `p11 = p22 = N/2`.
5. **Estimador final.** `I = (2/N)·Σ y·sin(iΔφ)`, `Q = (2/N)·Σ y·cos(iΔφ)`, com
   coeficientes de uma LUT.
6. **Harmônicas espalhadas.** Nenhuma das 7 primeiras cai sobre f_IF; as primeiras
   a cair são a (N−1)ª e a (N+1)ª.
7. **Ruído e offset.** Nuvens de estimativas IQ × Non-IQ; o offset DC se cancela.
8. **Latência.** Uma estimativa por amostra × uma a cada N amostras.
9. **Resumo** em tabela.

### Digital Down Conversion

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
8. **Mistura, filtragem e decimação.** Soma e diferença no espectro e o aliasing
   quando se decima sem filtrar.
9. **Filtro CIC.** Integradores, ↓R e pentes; equivalência com média móvel;
   resposta sinc, droop e crescimento de bits.
10. **DDC × IQ sampling clássico** e resumo.

## Estrutura

`src/` espelha `docs/`: cada animação fica na pasta com o mesmo nome do assunto
que ela anima.

```
Master-Brain/
├── docs/                                       # textos (.md) e figuras
│   ├── Componentes de um sistema de RF/
│   ├── Detecção de amplitude e fase em RF/
│   │   ├── Digital Down Conversion/
│   │   ├── IQ sampling/
│   │   └── Non-IQ sampling/
│   ├── Filtros/
│   └── Modelagem de uma cavidade de RF/
├── src/                                        # animações (Manim), mesma árvore
│   ├── Componentes de um sistema de RF/
│   │   └── componentes_sistema_rf.py
│   ├── Detecção de amplitude e fase em RF/
│   │   ├── Digital Down Conversion/
│   │   │   └── digital_down_conversion.py
│   │   ├── IQ sampling/
│   │   │   └── iq_sampling.py
│   │   └── Non-IQ sampling/
│   │       └── non_iq_sampling.py
│   ├── Filtros/
│   │   └── filtros.py
│   └── Modelagem de uma cavidade de RF/
│       └── modelagem_cavidade.py
├── media/                                      # saída do Manim (ignorada pelo git)
└── venv/                                       # ambiente Python (ignorado pelo git)
```

Cada arquivo de `src/` é independente: traz suas próprias funções de desenho
(fasores, eixos, diagramas de blocos, símbolos de circuito) e uma única cena,
cujo `construct` chama as subcenas em sequência. O docstring no topo de cada
arquivo descreve o roteiro e o comando para renderizar.

## Requisitos

Testado no Ubuntu 24.04 com Python 3.12 e Manim 0.21.0.

### Pacotes do sistema

```bash
# Bibliotecas usadas pelo Manim para desenhar e renderizar texto
sudo apt install build-essential python3-dev pkg-config libcairo2-dev libpango1.0-dev ffmpeg

# LaTeX para as fórmulas (MathTex): obrigatório em todas as animações
sudo apt install texlive texlive-latex-extra dvisvgm
```

### Ambiente Python

Na raiz do repositório:

```bash
python3 -m venv venv
source venv/bin/activate
pip install manim
```

## Executar

Com o venv ativado, a partir da raiz do repositório. Os caminhos têm espaços e
acentos, por isso vão entre aspas:

```bash
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libglib-2.0.so.0   # veja Problemas comuns

manim -pql "src/Componentes de um sistema de RF/componentes_sistema_rf.py" ComponentesSistemaRF
manim -pql "src/Modelagem de uma cavidade de RF/modelagem_cavidade.py" ModelagemCavidade
manim -pql "src/Filtros/filtros.py" Filtros
manim -pql "src/Detecção de amplitude e fase em RF/IQ sampling/iq_sampling.py" IQSampling
manim -pql "src/Detecção de amplitude e fase em RF/Non-IQ sampling/non_iq_sampling.py" NonIQSampling
manim -pql "src/Detecção de amplitude e fase em RF/Digital Down Conversion/digital_down_conversion.py" DigitalDownConversion
```

O `-p` abre o vídeo assim que ele termina de renderizar. O vídeo fica em
`media/videos/<nome do .py>/<qualidade>/<Cena>.mp4`; por exemplo, com `-ql`:

```
media/videos/componentes_sistema_rf/480p15/ComponentesSistemaRF.mp4
media/videos/modelagem_cavidade/480p15/ModelagemCavidade.mp4
media/videos/filtros/480p15/Filtros.mp4
media/videos/iq_sampling/480p15/IQSampling.mp4
media/videos/non_iq_sampling/480p15/NonIQSampling.mp4
media/videos/digital_down_conversion/480p15/DigitalDownConversion.mp4
```

### Qualidade de renderização

| Flag  | Resolução | Uso             |
|-------|-----------|-----------------|
| `-ql` | 480p15    | rascunho rápido |
| `-qm` | 720p30    | revisão         |
| `-qh` | 1080p60   | versão final    |
| `-qk` | 2160p60   | 4K              |

Outras opções úteis:

```bash
# Renderiza só o último quadro como PNG
manim -sql "src/Filtros/filtros.py" Filtros

# Exporta como GIF
manim -ql --format gif "src/Filtros/filtros.py" Filtros
```

## Personalização

Todas as animações seguem o mesmo padrão visual, definido no topo de cada arquivo:

| Constante | O que controla |
|---|---|
| `FUNDO` | cor de fundo (`#0e1117` em todas) |
| `COR_*` | paleta didática da animação (por exemplo, `COR_I` dourado e `COR_Q` verde para os canais I e Q) |
| `EIXO_CFG` | estilo dos eixos dos gráficos |

Constantes específicas:

| Arquivo | Constante | O que controla |
|---|---|---|
| `iq_sampling.py` | `FI0` | fase φ0 do sinal usado nas cenas |
| `iq_sampling.py`, `non_iq_sampling.py` | `ALTURAS` | amplitudes (ilustrativas) das harmônicas no espectro |
| `non_iq_sampling.py` | `N`, `M` | razão de amostragem `f_s/f_IF = N/M` (padrão 9/2) |
| `non_iq_sampling.py` | `SIGMA` | ruído das amostras nas cenas de mínimos quadrados e de ruído |
| `modelagem_cavidade.py` | `Q_CARREGADO` | fator de qualidade do gráfico de \|Z(jω)\| |

Valores numéricos marcados como ilustrativos ou exagerados (tolerâncias, número
de bits, Q, amplitudes de harmônicas) servem para que o efeito fique visível na
tela; a animação avisa quando é o caso.
