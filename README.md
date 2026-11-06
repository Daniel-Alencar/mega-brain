# Mega-Brain

Conteúdo e animações didáticas de processamento de sinais para sistemas LLRF
(*Low Level RF*) de aceleradores de partículas.

O repositório tem duas partes que andam juntas:

- **`docs/`**: um texto em Markdown para cada assunto, independente e completo.
- **`src/`**: uma animação em [Manim Community](https://www.manim.community/) para
  cada texto.

As duas árvores são espelhadas: o mesmo caminho de pastas, com o mesmo prefixo
numérico, leva ao texto em `docs/` e à animação em `src/`. O número é a ordem de
estudo recomendada.

## Assuntos

A numeração das pastas **é** a ordem de estudo, e ela é idêntica em `docs/` e em
`src/`: o texto e a animação de um assunto ficam no mesmo caminho, mudando só a
raiz. Por exemplo, o assunto 7.3.2 é
`docs/7 - Detecção de amplitude e fase em RF/3 - Digital Down Conversion/2 - Filtro CIC/Filtro CIC.md` e
`src/7 - Detecção de amplitude e fase em RF/3 - Digital Down Conversion/2 - Filtro CIC/filtro_cic.py`.

| # | Assunto | Texto | Animação | Cena | Duração |
|---|---|---|---|---|---|
| 1 | Componentes de um sistema de RF | [.md](docs/1%20-%20Componentes%20de%20um%20sistema%20de%20RF/Componentes%20de%20um%20sistema%20de%20RF.md) | [componentes_sistema_rf.py](src/1%20-%20Componentes%20de%20um%20sistema%20de%20RF/componentes_sistema_rf.py) | `ComponentesSistemaRF` | ~4 min |
| 2 | Fundamentos de Sinais e Sistemas Discretos | [.md](docs/2%20-%20Fundamentos%20de%20Sinais%20e%20Sistemas%20Discretos/Fundamentos%20de%20Sinais%20e%20Sistemas%20Discretos.md) | [fundamentos_sinais_discretos.py](src/2%20-%20Fundamentos%20de%20Sinais%20e%20Sistemas%20Discretos/fundamentos_sinais_discretos.py) | `FundamentosSinaisDiscretos` | ~11 min |
| 3 | Amostragem e Aliasing | [.md](docs/3%20-%20Amostragem%20e%20Aliasing/Amostragem%20e%20Aliasing.md) | [amostragem_aliasing.py](src/3%20-%20Amostragem%20e%20Aliasing/amostragem_aliasing.py) | `AmostragemAliasing` | ~6 min |
| 4 | Filtros | [.md](docs/4%20-%20Filtros/Filtros.md) | [filtros.py](src/4%20-%20Filtros/filtros.py) | `Filtros` | ~3 min |
| 5 | Modelagem de uma cavidade de RF | [.md](docs/5%20-%20Modelagem%20de%20uma%20cavidade%20de%20RF/Modelagem%20de%20uma%20cavidade%20de%20RF.md) | [modelagem_cavidade.py](src/5%20-%20Modelagem%20de%20uma%20cavidade%20de%20RF/modelagem_cavidade.py) | `ModelagemCavidade` | ~3 min |
| 6 | Mixer | [.md](docs/6%20-%20Mixer/Mixer.md) | [mixer.py](src/6%20-%20Mixer/mixer.py) | `Mixer` | ~8 min |
| 7.1 | Detecção: IQ sampling | [.md](docs/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/1%20-%20IQ%20sampling/IQ%20sampling.md) | [iq_sampling.py](src/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/1%20-%20IQ%20sampling/iq_sampling.py) | `IQSampling` | ~9 min |
| 7.2 | Detecção: Non-IQ sampling | [.md](docs/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/2%20-%20Non-IQ%20sampling/Non-IQ%20sampling.md) | [non_iq_sampling.py](src/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/2%20-%20Non-IQ%20sampling/non_iq_sampling.py) | `NonIQSampling` | ~3 min |
| 7.3 | Detecção: Digital Down Conversion | [.md](docs/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/3%20-%20Digital%20Down%20Conversion/Digital%20Down%20Conversion.md) | [digital_down_conversion.py](src/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/3%20-%20Digital%20Down%20Conversion/digital_down_conversion.py) | `DigitalDownConversion` | ~6 min |
| 7.3.1 | DDC: Decimador | [.md](docs/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/3%20-%20Digital%20Down%20Conversion/1%20-%20Decimador/Decimador.md) | [decimador.py](src/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/3%20-%20Digital%20Down%20Conversion/1%20-%20Decimador/decimador.py) | `Decimador` | ~2 min |
| 7.3.2 | DDC: Filtro CIC | [.md](docs/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/3%20-%20Digital%20Down%20Conversion/2%20-%20Filtro%20CIC/Filtro%20CIC.md) | [filtro_cic.py](src/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/3%20-%20Digital%20Down%20Conversion/2%20-%20Filtro%20CIC/filtro_cic.py) | `FiltroCIC` | ~7 min |
| 7.3.3 | DDC: Filtro FIR | [.md](docs/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/3%20-%20Digital%20Down%20Conversion/3%20-%20Filtro%20FIR/Filtro%20FIR.md) | [filtro_fir.py](src/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/3%20-%20Digital%20Down%20Conversion/3%20-%20Filtro%20FIR/filtro_fir.py) | `FiltroFIR` | ~2 min |
| 8 | Up-conversion | [.md](docs/8%20-%20Up-conversion/Up-conversion.md) | [up_conversion.py](src/8%20-%20Up-conversion/up_conversion.py) | `UpConversion` | ~5 min |

A ordem segue a cadeia de dependências — **o sistema → a matemática → o sinal
digitalizado → os blocos analógicos → a detecção → a geração**:

- **1** dá o mapa da malha LLRF inteira, para que cada bloco dos assuntos
  seguintes tenha onde se encaixar: é a resposta à pergunta "por que existe um
  mixer, um ADC, um DDC, um DAC".
- **2** e **3** são a base de DSP: o que é uma sequência, o que é um sistema LTI
  e o que a amostragem faz com o espectro.
- **4** traz polos, ζ, Q e roll-off, que **5** usa em seguida para modelar a
  cavidade — um RLC ressonante — e que reaparecem em todo filtro posterior.
- **6** é o último bloco analógico antes do ADC, e o lugar onde se vê a
  frequência imagem pela primeira vez.
- **7** são as três técnicas de detecção de amplitude e fase, com o DDC aberto
  nos seus próprios blocos: o decimador primeiro (o que é decimar), o CIC depois
  (o filtro que existe para permitir a decimação) e o FIR no fim (o filtro que
  corrige o *droop* do CIC).
- **8** fecha a volta: do I/Q digital de novo até a portadora, reaproveitando o
  fasor, o NCO e a frequência imagem já vistos.

### Relação com o currículo de DSP

[`docs/0 - Tópicos`](docs/0%20-%20Tópicos/Tópicos.md) descreve uma formação de
base em DSP em 7 tópicos. A trilha acima cobre parte dela, e é útil saber qual:

| Tópico de DSP | Onde está |
|---|---|
| 1 · Sinais e sistemas discretos | assunto **2** |
| 2 · Amostragem e reconstrução | assunto **3** |
| 3 · Transformadas (DTFT, Z, DFT, FFT) | **não coberto**; usado implicitamente em toda cena de espectro |
| 4 · Projeto de filtros digitais | parcial: **7.3.3** (FIR, fase linear, custo) e **4** (protótipos analógicos) |
| 5 · Efeitos de precisão finita | parcial: crescimento de bits e overflow no CIC (**7.3.2**) e espúrios do DDS (**6**) |
| 6 · Processamento multitaxa | **7.3.1** (decimação, polifásico) e **7.3.2** (CIC, Hogenauer) |
| 7 · Aplicações em RF | **7.1**, **7.2**, **7.3** e **8** |

## O que cada animação mostra

### 1 · Componentes de um sistema de RF

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

### 2 · Fundamentos de Sinais e Sistemas Discretos

1. **Do contínuo ao discreto.** A onda analógica, as marcas de amostragem e a
   sequência resultante; `n` é índice inteiro, e entre amostras não existe nada.
2. **δ[n] e u[n].** Os dois sinais elementares e a relação nos dois sentidos:
   `δ[n] = u[n] − u[n−1]` e `u[n] = Σ δ[k]`.
3. **Exponenciais e senoides discretas.** `aⁿ` decaindo e crescendo, o fasor
   `e^{jωn}` passo a passo, e as duas armadilhas: ω e ω+2π dão a mesma
   sequência, e uma senoide discreta só é periódica se ω/2π for racional.
4. **Decomposição em impulsos.** `x[n] = Σ x[k]·δ[n−k]`, desmontada amostra a
   amostra — é a ideia que justifica toda a teoria LTI.
5. **Linearidade e invariância.** Definições e contraexemplos numéricos
   (`y = x²` e `y[n] = n·x[n]`).
6. **Causalidade e BIBO.** Passado e futuro no eixo, `h[n] = 0` para `n < 0`,
   e `Σ|h[n]| < ∞` comparando `0,8ⁿ` com `1,25ⁿ`.
7. **Convolução.** Inverter, deslizar e somar, conta a conta, com
   `x = 1,2,3` e `h = 1,1,1`; saída de comprimento N+M−1.
8. **LCCDE.** A receita prática, com os `b` e os `a` separados, e FIR × IIR
   lado a lado.

### 3 · Amostragem e Aliasing

Exemplo usado nas cenas 1 a 7: f_s = 10 kHz (T = 0,1 ms), sinal útil de 0 a 4 kHz.

1. **A mesma sequência serve a infinitas ondas.** Senoides de 1, 9 e 11 kHz
   passando pelos mesmos onze pontos, e a álgebra que explica:
   `cos(2π·9n/10) = cos(2πn − 2π·n/10) = cos(2π·n/10)`. O ADC não erra cada
   medida — ele perde a identidade da frequência.
2. **Amostrar é multiplicar por um pente de impulsos.** No tempo, `x(t)·Σδ(t−nT)`;
   na frequência, a convolução com o pente replica o espectro a cada f_s:
   `X_s(f) = f_s·Σ X(f − k·f_s)`. As réplicas são as infinitas ondas da cena 1.
3. **O critério de Nyquist.** Baixando f_s com o espectro na tela: as réplicas se
   aproximam, encostam exatamente em f_max quando f_s = 2·f_max, e se sobrepõem
   abaixo disso. Fecha com `f_s > 2·f_max` e a promessa de reconstrução exata.
4. **A regra da dobra.** O mapa `f_ap = |f − f_s·round(f/f_s)|` desenhado como
   onda triangular, com as zonas de Nyquist sombreadas e um ponto percorrendo
   1 → 4 → 6 → 9 → 11 → 21 kHz. As zonas pares chegam com o espectro invertido.
5. **O filtro anti-aliasing.** Interferência em 7 kHz dobrando para 3 kHz, dentro
   da banda útil; o passa-baixa analógico atenuando-a enquanto ainda era 7 kHz; e
   a banda de transição, que obriga a escolher entre folga de guarda e
   sobreamostragem.
6. **Quantização.** Degraus e erro com B = 2, 3, 4 e 6 bits, `Δ = V_FS/2^B`,
   `σ² = Δ²/12`, `SQNR ≈ 6,02·B + 1,76 dB` e a tabela de 8 a 16 bits.
7. **Reconstrução.** Uma sinc por amostra somando-se de volta ao sinal; depois o
   Zero-Order Hold real do DAC, o seu droop de −3,9 dB em f_s/2 e as imagens em
   torno de f_s, com os dois remédios.
8. **Sub-amostragem deliberada.** Nyquist sobre f_max (1000 MSps) × sobre a
   largura de banda (4 MSps); a portadora de 500 MHz caindo em 20 MHz com
   f_s = 80 MSps — que é f_s/4, a mesma escolha do assunto 7.1; e o preço:
   anti-aliasing passa-banda, inversão nas zonas pares e jitter.
9. **Resumo.**

### 4 · Filtros

1. **Ordem.** Grau de D(s) = nº de polos = nº de elementos reativos (RC × RLC).
2. **Roll-off.** Bode de 1ª ordem (−20 dB/década) × 2ª ordem (−40 dB/década).
3. **Comportamento dinâmico.** Polos no plano s e resposta ao degrau variando ζ (e Q).
4. **1ª ordem.** RC série: tensão no C (passa-baixa) e no R (passa-alta), com varredura de ω.
5. **2ª ordem.** Mesmo D(s); o numerador define LP, BP ou HP; efeito de Q; tabela-resumo.
6. **RLC série, quatro filtros.** V_C, V_L, V_R e V_LC ⇒ LP, HP, BP e notch.
7. **Série × paralelo.** |Z| mínima × máxima em ω₀ e a divisão de corrente nos ramos.

### 5 · Modelagem de uma cavidade de RF

1. **Por que RLC paralelo.** Campo E axial ↔ C, campo B azimutal ↔ L, perdas nas
   paredes ↔ R, com a energia oscilando entre W_E e W_M.
2. **Circuito equivalente.** Gerador de Norton (`I'rf ∥ Z₀`), acoplador 1:n,
   cavidade e o feixe passando em pacotes.
3. **Rebatimento.** `V₂ = n·V₁`, `I₂ = I₁/n` ⇒ `Z₀' = n²·Z₀`; o transformador desaparece.
4. **Lei dos nós.** Correntes nos ramos até a equação diferencial de 2ª ordem.
5. **Laplace.** A impedância `V_C(s)/I_C(s)`.
6. **Forma canônica.** `ω₀ = 1/√(LC)`, `2ω½` e `K = 1/C`.
7. **Resposta em frequência.** L em curto, C em curto e L∥C aberto em ω₀.

### 6 · Mixer

Frequências do exemplo: f_RF = 100 MHz, f_LO = 130 MHz, f_IF = 30 MHz.

1. **Mixer ideal.** O produto ponto a ponto vira um batimento; o batimento é
   decomposto nas duas senoides que o formam (`f_LO − f_RF` e `f_LO + f_RF`) e
   o espectro mostra que não há mais nada além delas.
2. **Nenhum componente multiplica tensões.** Curva I × V exponencial do diodo,
   ponto de operação e as aproximações de Taylor de ordem 1, 2 e 3; a soma dos
   dois tons atravessa a curva e sai deformada.
3. **Quem gera o quê.** Termo a termo (`a·v_in`, `b·v_in²`, `c·v_in³`), com um
   espectro embaixo que vai sendo preenchido: vazamento, a IF que nasce do
   termo quadrático, harmônicos e intermodulação.
4. **A família m·f_RF ± n·f_LO.** O espectro real construído ordem por ordem,
   com cada raia rotulada e colorida por categoria; SFDR ≈ 5 dBc.
5. **Frequência imagem.** Duas entradas simétricas em torno do LO caem na mesma
   IF; o cosseno real é a soma de dois fasores girando em sentidos opostos, e é
   o fasor negativo que cria a imagem. Mistura complexa I/Q resolve.
6. **No FPGA.** Cadeia ADC → mixer → CIC → FIR com o DDS; a rampa de fase
   truncada e a LUT quantizada mostram de onde vêm os espúrios digitais
   (`SFDR ≈ −6,02·B`); e o caso `f_LO = f_s/4`, em que a multiplicação vira
   `{1, 0, −1, 0}`.
7. **Atraso de grupo.** Elíptico analógico (pico perto da banda) × FIR de fase
   linear (constante), e o custo em margem de fase numa malha de realimentação.

### 7.1 · IQ sampling

A ordem abaixo é a do vídeo.

1. **Polar × cartesiana.** `A·sin(ωt + φ0) = I·sin ωt + Q·cos ωt` e o fasor (I, Q).
2. **O que o ADC mede.** Só a projeção vertical do fasor: uma amostra define uma
   reta; duas amostras a 90° definem o ponto (I, Q).
3. **f_s = 4·f_IF.** O fasor avança 90° por amostra e o ADC entrega Q, I, −Q, −I, …
4. **Os quatro vetores do par de amostras.** Cada par `(y_{i+1}, y_i)` é um ponto
   do plano I/Q, e os quatro ficam a 90° um do outro. Uma cópia do primeiro gira
   na tela e pousa sobre o segundo, mostrando que `(I,Q) → (−Q,I)` e não
   `(−I,Q)`. Fecha com a leitura correta da notação: as letras são comprimentos
   medidos em t₀, girados para os novos eixos — não o nome do eixo onde a ponta
   está.
5. **Algoritmo de rotação.** Janela de 2 amostras e matrizes só com 0 e ±1.
6. **Primeiro uso: detectar um erro de fase.** Referência I=1, Q=1 → 45°. Entra
   uma perturbação de 10°, as amostras viram 0,81 e 1,16, e a leitura cai para
   35° com a amplitude intacta: o ponto desliza sobre o círculo. A malha age
   sobre a diferença.
7. **Segundo uso: ler uma mensagem na fase.** Constelação QPSK (45°=00, 135°=01,
   225°=11, 315°=10); o receptor amostra, roda de volta, calcula atan(Q/I) e
   traduz em bits. Mesmo hardware, outro destino.
8. **Generalização f_s = m·f_IF.** Cada amostra é uma faixa (± ruído); a
   incerteza no cruzamento cresce com `1/|sin Δφ|`.
9. **Offset DC.** O erro troca de sinal a cada passo: o ponto (I, Q) salta num
   quadrado e aparece ripple em f_IF.
10. **O que é aliasing.** A regra da dobra, antes de qualquer harmônica: uma
    varredura lenta mostra a frequência real subindo sem parar enquanto a
    aparente vai e volta dentro de [0, f_s/2], como uma sanfona. Termina com
    1, 3, 5 e 7·f_IF convergindo todas para o mesmo ponto.
11. **Harmônicas ímpares sobre f_IF.** A regra é aplicada uma harmônica de cada
    vez, com a aritmética na tela (`3 mod 4 = 3 > 2 ⇒ 4 − 3 = 1`); depois o
    porquê no círculo (`3×90° = 270° ≡ −90°`, o efeito da roda de carroça), a
    prova no tempo (as duas curvas passam pelos mesmos 9 pontos), o estrago no
    fasor medido (`Δφ ≈ A₃/A₁`, −40 dBc → 0,57°) e as quatro saídas possíveis.
12. **Resumo.**

Para gerar o vídeo: `make IQSampling`, ou `make IQSampling Q=h` para a versão em
1080p (veja [Executar](#executar)).

Na mesma pasta, [`iq_sampling2.ipynb`](src/7%20-%20Detecção%20de%20amplitude%20e%20fase%20em%20RF/1%20-%20IQ%20sampling/iq_sampling2.ipynb)
reproduz numericamente **todas as cenas acima**, na mesma ordem: a identidade
polar ↔ cartesiana, a amostragem em `f_s = 4·f_IF`, os quatro pares
`(y_{i+1}, y_i)`, a matriz de rotação, a detecção de erro de fase, a demodulação
QPSK, a amplificação de ruído `1/|sin Δφ|`, o ripple do offset DC, a regra da
dobra e o aliasing das harmônicas ímpares. Serve para mexer nos parâmetros e ver
o efeito — algo que o vídeo, sendo fixo, não permite.

```bash
jupyter lab "src/7 - Detecção de amplitude e fase em RF/1 - IQ sampling/iq_sampling2.ipynb"
```

Requer apenas `numpy` e `matplotlib` (mais `jupyter` para abrir o caderno).

Na mesma pasta há também `iq_sampling1.ipynb`, material de apoio de terceiros
(em inglês) sobre o mesmo assunto — não é parte do roteiro do vídeo.

### 7.2 · Non-IQ sampling

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

### 7.3 · Digital Down Conversion

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
7. **NCO.** Por que ele merece uma cena (quadratura exata e sintonia livre), o
   acumulador de fase como roda de N bits, a LUT, os dois canais lidos da mesma
   roda com 4 marcas de distância (90° exatos) e `f_out = M/2^N · f_CLK`. A
   truncação de fase fica só no texto: é assunto de DDS, não de DDC.
8. **Mistura, filtragem e decimação.** A conta da cena 3 relida no espectro
   (banda base × termo em 2ωc), o LPF e o aliasing quando se decima sem filtrar.
9. **Filtro CIC.** Integradores, ↓R e pentes; equivalência com média móvel;
   resposta sinc, droop e crescimento de bits.
10. **DDC × IQ sampling clássico** e resumo.

### 7.3.1 · Decimador

1. **O que é decimar.** Manter 1 amostra a cada M, com M variando: `f_s' = f_s/M`.
2. **As duas etapas.** FIR passa-baixa (anti-aliasing) seguido de ↓M.
3. **Aliasing.** No espectro, o ruído em 0,3·f_s se dobra para 0,05·f_s após ↓4; no
   tempo, as amostras mantidas desenham uma onda falsa. Com o FIR antes, o sinal passa intacto.
4. **Downsampling.** Quais amostras ficam: `y[m] = x[m·M]`.
5. **FPGAs.** Um multiplicador atende M contas, clock de 200 MHz × 50 MHz e menor consumo.
6. **Polifásico.** A implementação ingênua desperdiça M − 1 saídas; os sub-filtros
   E₀…E₃ com comutador fazem N/M multiplicações por amostra.

### 7.3.2 · Filtro CIC

Exemplo usado: atraso do comb D = 4.

1. **Lendo o diagrama.** Os quatro símbolos — seta, somador (com os sinais + e −),
   registrador `z⁻¹` e nó — e uma amostra atravessando o registrador em dois ciclos.
2. **Estrutura.** Integrador `I[n] = I[n−1] + x[n]` e comb `y[n] = I[n] − I[n−4]`,
   com o contraste entre o laço realimentado e o caminho só para frente.
3. **Integrador ciclo a ciclo.** Os números entrando no somador, voltando pelo laço e
   entrando no registrador, com tabela `n | x[n] | z⁻¹ | I[n]`; depois o acumulador
   crescendo até o limite de bits e o overflow proposital.
4. **Comb ciclo a ciclo.** O `z⁻⁴` aberto em quatro registradores: os valores andando
   pela fila, o primeiro caindo pela ponta no 4º ciclo, e o x[0] se anulando na álgebra.
5. **Janela deslizante.** A tabela com as três linhas, a janela de 4 amostras correndo e
   a resposta ao impulso `1 1 1 1` — um FIR de coeficientes iguais, sem multiplicadores.
6. **Por que filtra.** Janela sobre `+1 −1 +1 −1` (soma 0) e `+1 +1 +1 +1` (soma 4),
   depois o mesmo efeito em um sinal ruidoso real.
7. **Medindo |H(f)|.** Uma senoide de teste por vez: ganho 4 em DC, 2,61 em f_s/8, zero em
   f_s/4 (um período inteiro na janela) e em f_s/2 (dois períodos), com a curva sendo
   traçada ponto a ponto enquanto a frequência varre de 0 a f_s/2.
8. **Lendo o gráfico.** O que é cada eixo, o ganho D em DC, os zeros em múltiplos de f_s/D,
   lóbulo principal e lóbulos laterais (≈ −11 dB) e a fórmula `|sin(πDf/f_s)/sin(πf/f_s)|`.
9. **Trocando o fator.** D = 2, 4, 8 e 16 na frequência (primeiro zero em f_s/D) e no tempo
   (o mesmo sinal ruidoso filtrado e decimado por cada fator, até o droop visível em D = 16).
10. **Anti-aliasing sob medida.** As bandas em torno de f_s/4, f_s/2 e 3f_s/4 dobram sobre a
    banda base ao decimar por 4 — e os zeros do CIC caem exatamente no centro delas.
11. **Com o decimador.** ↓4 entre integrador e comb: o comb, com atraso de 1 na taxa
    lenta, subtrai 4 amostras rápidas (Hogenauer).
12. **N estágios.** `|H(f)|ᴺ` em dB: lóbulos em −11, −23 e −34 dB e o droop que o FIR corrige.

### 7.3.3 · Filtro FIR

1. **A equação.** `y[n] = Σ h[k]·x[n−k]`, N taps e ordem N − 1.
2. **Estrutura.** Linha de atrasos, multiplicadores e somadores, com as amostras
   andando clock a clock e cada y[n] calculado.
3. **Resposta ao impulso.** A do FIR dura N amostras; a de um IIR nunca zera.
4. **Suavização.** Sinal ruidoso com N = 1, 5, 10 e 20 taps e o atraso (N − 1)/2.
5. **Fase linear.** Um pulso retangular passa pelo FIR simétrico (só atrasa) e pelo IIR (deforma).
6. **Custo.** Passa-baixa com 11, 31 e 101 taps: transição mais estreita exige mais multiplicadores.
7. **FIR × IIR.** Equações e tabela comparativa.

### 8 · Up-conversion

Exemplo usado: f_IF = 20 MHz, f_LO = 480 MHz, f_RF = 500 MHz, imagem em 460 MHz.

1. **O problema.** De um lado I e Q em banda base, do outro a cavidade em 500 MHz;
   um DAC direto (DDS) ainda não tem precisão e velocidade para fazer a ponte.
2. **I e Q são o fasor.** `I·sin + Q·cos` é uma única senoide, com
   `A = √(I²+Q²)` e `φ₀ = atan(Q/I)`.
3. **Modulador vetorial (homodino).** Híbrido de 90°, dois mixers e um somador
   (Fig. 21); no espectro, a banda base sobe inteira para f_LO = f_RF.
4. **AM e PM.** Os mesmos dois botões: `A₀(t)` estica o fasor, `φ₀(t)` o gira.
5. **Os erros do analógico.** Offset (vazamento de portadora), desbalanço de
   ganho (elipse), skew de quadratura (eixos tortos) e ruído de fase do LO.
6. **Pré-distorção.** A matriz de correção do skew, feita no FPGA antes dos DACs.
7. **Heteródino (Fig. 22).** NCO e quadratura digitais, um DAC na IF e um mixer
   analógico: nasce a imagem em f_LO − f_IF e com ela o método da filtragem.
8. **Banda lateral única (Figs. 23 e 24).** Dois DACs e um modulador vetorial;
   as bandas inferiores se cancelam por estarem 180° fora de fase.
9. **Comparação.** Homodino × banda dupla × banda lateral única, e a supressão
   de banda lateral em dBc.

## Requisitos

Testado no Ubuntu 24.04 com Python 3.12 e Manim 0.22.0.

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

A partir da raiz do repositório, o alvo é o **nome da cena** — a coluna *Cena*
da tabela de assuntos:

```bash
make                            # lista as cenas disponíveis
make DigitalDownConversion      # renderiza em 480p e abre o vídeo ao terminar
make FiltroCIC Q=h              # versão final, 1080p
make AmostragemAliasing P=0     # não abre o vídeo ao terminar
make todas                      # renderiza tudo
make limpar                     # apaga os vídeos gerados
```

O nome do arquivo também serve, e maiúsculas não importam: `make filtro_cic` faz
o mesmo que `make FiltroCIC`. Com `bash-completion` instalado, `make <TAB>`
completa os nomes.

O `make` é só uma casca para [`render.sh`](render.sh), que pode ser usado direto
e aceita mais opções:

```bash
./render.sh --lista             # cenas e a pasta de cada uma
./render.sh FiltroCIC -q h -n   # 1080p, sem abrir no fim
./render.sh --todas             # renderiza tudo
./render.sh --onde decimador    # mostra a qual arquivo e cena um nome resolve
./render.sh --ambiente          # mostra qual manim será usado
./render.sh Mixer -- -s         # depois de -- vai tudo direto para o manim
```

O script existe para resolver três chatices de uma vez: os caminhos dos `.py`
têm espaços e acentos; o Cairo precisa do `LD_PRELOAD` da `libglib`; e o manim
pode estar no `venv/` ou no `PATH`. Ele testa os candidatos e usa o primeiro que
responde, então não é preciso ativar o venv antes.

Para chamar o manim na mão, o formato é o de sempre — note as aspas, por causa
dos espaços no caminho:

```bash
manim -pql "src/4 - Filtros/filtros.py" Filtros
```

### Qualidade de renderização

| `Q=` | Resolução | Uso |
|---|---|---|
| `l` (padrão) | 480p15 | rascunho rápido |
| `m` | 720p30 | revisão |
| `h` | 1080p60 | versão final |
| `k` | 2160p60 | 4K |

Os vídeos saem em `media/videos/<nome do .py>/<qualidade>/<Cena>.mp4` — por
exemplo, `media/videos/filtro_cic/480p15/FiltroCIC.mp4`. O caminho exato é
impresso ao fim de cada renderização.

Outras opções úteis, passadas ao manim depois de `--`:

```bash
./render.sh Filtros -- -s              # só o último quadro, como PNG
./render.sh Filtros -- --format gif    # exporta como GIF
./render.sh Filtros -- -n 0,5          # só as animações 0 a 5 (teste rápido)
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
| `mixer.py` | `F_RF`, `F_LO` | frequências de RF e do LO (padrão 100 e 130 MHz) |
| `mixer.py` | `COEFS` | coeficientes do polinômio de transferência do mixer real |
| `mixer.py` | `FD_RF`, `FD_LO` | frequências reduzidas usadas nas cenas no domínio do tempo |

Valores numéricos marcados como ilustrativos ou exagerados (tolerâncias, número
de bits, Q, amplitudes de harmônicas) servem para que o efeito fique visível na
tela; a animação avisa quando é o caso.
