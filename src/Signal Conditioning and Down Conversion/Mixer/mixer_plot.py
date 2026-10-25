# -*- coding: utf-8 -*-
"""
Mixer: ideal x real x digital, e o custo em atraso de grupo
===========================================================

Execução (a partir da raiz do repositório):
    python3 "src/Signal Conditioning and Down Conversion/Mixer/Mixer.py"
    python3 "src/Signal Conditioning and Down Conversion/Mixer/Mixer.py" --salvar

Abre quatro janelas independentes (uma por figura), para que cada uma caiba
legível na tela. Com --salvar, grava os PNGs em ./figuras em vez de exibir.

    Fig. 1  Mixer ideal      - multiplicação pura: só |f_LO-f_RF| e f_LO+f_RF
    Fig. 2  Mixer real       - não linearidade polinomial; cada raia rotulada
                               com (m,n), reproduzindo a família m*f_RF +- n*f_LO
    Fig. 3  Mixer digital    - DDS com acumulador de fase + LUT quantizada e
                               produto em ponto fixo; espúrios de aritmética
                               finita, não de física do semicondutor
    Fig. 4  Atraso de grupo  - elíptico analógico x FIR de fase linear

A tabela completa de espúrios identificados é impressa no terminal.
"""

import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# ---------------------------------------------------------------- parâmetros

fs = 2000e6          # Frequência de amostragem: 2 GHz (alta para capturar harmônicos)
t = np.arange(0, 10e-6, 1/fs)  # Tempo de simulação: 10 microssegundos
N = len(t)

f_RF = 100e6         # Sinal de entrada RF: 100 MHz
f_LO = 130e6         # Oscilador Local LO: 130 MHz
f_IF = abs(f_LO - f_RF)        # Frequência intermediária esperada: 30 MHz

v_RF = np.cos(2 * np.pi * f_RF * t)
v_LO = np.cos(2 * np.pi * f_LO * t)

F_MAX = 500e6        # Limite do eixo de frequência nos espectros
MAX_ROTULOS = 14     # Quantas raias rotular por figura (as mais fortes)

# Paleta (segue as cores da Fig. 4 do artigo)
COR_IDEAL = "tab:blue"
COR_REAL = "tab:red"
COR_DIGITAL = "tab:green"
COR_UTIL = "#1a7f37"         # IF e seus harmônicos
COR_VAZAMENTO = "#c92a2a"    # LO, RF e harmônicos puros (m = 0 ou n = 0)
COR_IMD = "#1c6fb5"          # produtos cruzados

FIGSIZE = (12.5, 5.6)
CAIXA = dict(boxstyle="round,pad=0.45", fc="white", alpha=0.92, ec="0.7")

# ------------------------------------------------- cenários de mistura

# Cenário A: Misturador Ideal (Multiplicação matemática pura)
v_out_ideal = v_RF * v_LO

# Cenário B: Misturador Real (Modelo não linear de um diodo/transistor)
# V_in é a soma dos sinais antes de passar pela não linearidade.
# O diodo real é exponencial: acrescentamos ordens 4 e 5 para que apareçam
# também os harmônicos da própria IF (2IF, 3IF), que são (m,n) = (2,-2) e (3,-3).
v_in = v_RF + v_LO
a, b, c = 0.1, 0.5, 0.08     # Coeficientes polinomiais de transferência
d, e = 0.02, 0.006           # Ordens 4 e 5 (geram 2IF e 3IF)
v_out_real = (a * v_in + b * v_in**2 + c * v_in**3
              + d * v_in**4 + e * v_in**5)

# Cenário C: Misturador Digital (FPGA) ------------------------------------
# A multiplicação é aritmética exata num DSP slice. O que limita o espectro
# não é a física do semicondutor, e sim a quantização:
#   ACC_BITS  : largura do acumulador de fase do DDS
#   ADDR_BITS : bits que endereçam a LUT (truncamento de fase -> raias discretas)
#   LUT_BITS  : bits de amplitude da LUT                      (piso de ruído)
#   ADC_BITS  : quantização do sinal de entrada
#   OUT_BITS  : truncamento do produto
ACC_BITS, ADDR_BITS, LUT_BITS = 32, 14, 16
ADC_BITS, OUT_BITS = 14, 18


def quantiza(x, bits):
    """Quantiza x (|x| <= 1) em `bits` com arredondamento e saturação."""
    nivel = 2 ** (bits - 1) - 1
    return np.clip(np.round(x * nivel), -nivel, nivel) / nivel


def dds(freq, n_amostras, acc_bits=ACC_BITS, addr_bits=ADDR_BITS,
        lut_bits=LUT_BITS):
    """DDS: acumulador de fase + LUT de cosseno quantizada."""
    delta = int(round(freq / fs * 2**acc_bits))      # incremento de fase
    fase = (np.arange(n_amostras, dtype=np.int64) * delta) % 2**acc_bits
    endereco = fase >> (acc_bits - addr_bits)        # truncamento de fase
    lut = quantiza(np.cos(2 * np.pi * np.arange(2**addr_bits) / 2**addr_bits),
                   lut_bits)
    return lut[endereco]


x_adc = quantiza(v_RF, ADC_BITS)                     # entrada digitalizada
lo_dds = dds(f_LO, N)                                # LO sintetizado
v_out_digital = quantiza(x_adc * lo_dds, OUT_BITS)   # produto em ponto fixo


# -------------------------------------------------------------- espectro

def calcular_espectro(sinal):
    janela = np.hanning(N)
    fft_sinal = np.fft.fft(sinal * janela)
    freqs = np.fft.fftfreq(N, 1/fs)

    # Pegar apenas o lado positivo do espectro
    freqs_pos = freqs[:N//2]
    # Normalização coerente com a janela (ganho 0,5 do Hanning)
    mag_pos = np.abs(fft_sinal[:N//2]) / (N/2) / 0.5
    mag_db = 20 * np.log10(mag_pos + 1e-16)   # Evitar log(0)
    return freqs_pos, mag_db


# ------------------------------------- identificação automática de (m,n)

def identificar(f_alvo, ordem_max=6, tol=0.5e6):
    """Acha o par (m,n) de menor ordem tal que |m*f_RF + n*f_LO| ~= f_alvo.

    Por convenção m acompanha f_RF e n acompanha f_LO; o sinal de n é o que
    distingue, por exemplo, (1,-1) -> IF de (1,1) -> banda soma.
    """
    melhor = None
    for m in range(0, ordem_max + 1):
        for n in range(-ordem_max, ordem_max + 1):
            if (m == 0 and n == 0) or m + abs(n) > ordem_max:
                continue
            if abs(abs(m * f_RF + n * f_LO) - f_alvo) > tol:
                continue
            ordem = m + abs(n)
            if melhor is None or ordem < melhor[0]:
                melhor = (ordem, m, n)
    if melhor is None:
        return None
    _, m, n = melhor
    return m, n


def rotular(m, n):
    """Nome usual da raia, quando existe; senão a notação m*RF +- n*LO."""
    k = abs(n)
    if m == k and n < 0:                              # (1,-1), (2,-2), (3,-3)
        return "IF" if m == 1 else f"{m}IF"
    if m == 0:
        return "LO" if k == 1 else f"{k}LO"
    if n == 0:
        return "RF" if m == 1 else f"{m}RF"
    termo_rf = ("" if m == 1 else str(m)) + "RF"
    termo_lo = ("" if k == 1 else str(k)) + "LO"
    return f"{termo_rf}{'+' if n > 0 else '-'}{termo_lo}"


def classificar(m, n):
    """Cor da raia: útil (harmônico de IF), vazamento/harmônico puro ou IMD."""
    if m == abs(n) and n < 0:
        return COR_UTIL
    if m == 0 or n == 0:
        return COR_VAZAMENTO
    return COR_IMD


def detectar(freqs, mag_db, piso=-75, dist_min_mhz=4):
    """Lista de raias (f, m, n, rotulo, nivel_db), ordenada por frequência."""
    mascara = freqs <= F_MAX
    f, m_db = freqs[mascara], mag_db[mascara]
    distancia = max(1, int(dist_min_mhz * 1e6 / (fs / N)))
    picos, _ = signal.find_peaks(m_db, height=piso, distance=distancia)

    raias = []
    for p in picos:
        achado = identificar(f[p])
        if achado is None:
            continue
        m, n = achado
        raias.append((f[p], m, n, rotular(m, n), m_db[p]))
    return raias


def colorir_raias(ax, raias, piso_db):
    """Redesenha cada raia identificada na cor da sua categoria.

    O traço do espectro fica em cinza; o que dá cor ao gráfico são as raias
    classificadas, de modo que a legenda de cores signifique alguma coisa.
    """
    for f_pico, m, n, _rot, nivel_db in raias:
        ax.vlines(f_pico / 1e6, piso_db, nivel_db,
                  color=classificar(m, n), lw=1.6, zorder=3)


def anotar(ax, raias, max_rotulos=MAX_ROTULOS, n_niveis=3, sep_mhz=55):
    """Rotula as raias mais fortes, escalonando a altura e ligando por guia.

    As etiquetas sobem em `n_niveis` degraus acima do topo do gráfico; cada raia
    recebe uma linha-guia fina até o seu pico, de modo que nenhum texto precisa
    ficar encostado na raia (que foi o que embolou a versão anterior).
    """
    if not raias:
        return
    # Prioriza as mais fortes, depois reordena por frequência para escalonar
    fortes = sorted(raias, key=lambda r: -r[4])[:max_rotulos]
    fortes.sort(key=lambda r: r[0])

    topo = max(r[4] for r in raias)
    base = topo + 8
    passo = 11
    ax.set_ylim(top=base + n_niveis * passo + 6)

    nivel, f_anterior = 0, -1e12
    for f_pico, m, n, rot, nivel_db in fortes:
        if (f_pico - f_anterior) / 1e6 < sep_mhz:
            nivel = (nivel + 1) % n_niveis
        else:
            nivel = 0
        f_anterior = f_pico
        y_texto = base + nivel * passo
        cor = classificar(m, n)
        ax.annotate(f"{rot}\n({m},{n})",
                    xy=(f_pico / 1e6, nivel_db + 1),
                    xytext=(f_pico / 1e6, y_texto),
                    ha="center", va="bottom", fontsize=7.5, color=cor,
                    linespacing=0.95,
                    arrowprops=dict(arrowstyle="-", color=cor, lw=0.6,
                                    alpha=0.55, shrinkA=2, shrinkB=1))


def medir_sfdr(freqs, mag_db, uteis=(f_IF, f_RF + f_LO), guarda=3e6):
    """SFDR: diferença entre a IF e o maior espúrio (exclui DC e produtos úteis)."""
    mascara = (freqs > guarda) & (freqs <= F_MAX)
    for fu in uteis:
        mascara &= np.abs(freqs - fu) > guarda
    ref = mag_db[np.argmin(np.abs(freqs - f_IF))]
    return ref - mag_db[mascara].max()


def tabela(raias, titulo):
    """Imprime no terminal a lista completa de raias identificadas."""
    print(f"\n{titulo}")
    print(f"  {'f [MHz]':>9}  {'(m,n)':>8}  {'ordem':>5}  "
          f"{'nível [dB]':>10}  rótulo")
    for f_pico, m, n, rot, nivel_db in sorted(raias, key=lambda r: -r[4]):
        print(f"  {f_pico/1e6:9.1f}  {f'({m},{n})':>8}  {m+abs(n):5d}  "
              f"{nivel_db:10.1f}  {rot}")


freq_ideal, mag_ideal = calcular_espectro(v_out_ideal)
freq_real, mag_real = calcular_espectro(v_out_real)
freq_dig, mag_dig = calcular_espectro(v_out_digital)

raias_ideal = detectar(freq_ideal, mag_ideal, piso=-60)
raias_real = detectar(freq_real, mag_real, piso=-75)

sfdr_real = medir_sfdr(freq_real, mag_real)
sfdr_dig = medir_sfdr(freq_dig, mag_dig)


# ------------------------------------------- atraso de grupo dos filtros

# Especificação comum: passar a IF (30 MHz), rejeitar a partir de 60 MHz.
F_PASSA, F_PARA, ATENUACAO = 35e6, 60e6, 80.0   # Hz, Hz, dB

# (i) Elíptico analógico - roll-off abrupto, fase não linear
ORDEM_ELIP = 7
b_el, a_el = signal.ellip(ORDEM_ELIP, 0.1, ATENUACAO,
                          2 * np.pi * F_PASSA, analog=True)
w_el = 2 * np.pi * np.linspace(1e6, 150e6, 4000)
_, h_el = signal.freqs(b_el, a_el, worN=w_el)
tau_el = -np.gradient(np.unwrap(np.angle(h_el)), w_el)   # tau_g = -dfase/domega

# (ii) FIR de fase linear, já na taxa decimada do DDC (CIC com R = 8)
R_CIC, M_CIC, N_CIC = 8, 1, 5          # decimação, atraso diferencial, estágios
fs_dec = fs / R_CIC                     # 250 MHz
n_taps, beta = signal.kaiserord(ATENUACAO, (F_PARA - F_PASSA) / (fs_dec / 2))
n_taps |= 1                             # ímpar -> fase linear tipo I
h_fir = signal.firwin(n_taps, F_PASSA, window=("kaiser", beta), fs=fs_dec)
w_fir, gd_fir = signal.group_delay((h_fir, 1), w=4000, fs=fs_dec)
tau_fir = gd_fir / fs_dec               # amostras -> segundos

tau_fir_teorico = (n_taps - 1) / 2 / fs_dec
tau_cic = N_CIC * M_CIC * (R_CIC - 1) / 2 / fs
tau_el_if = np.interp(f_IF, w_el / (2 * np.pi), tau_el)


# ----------------------------------------------------------- visualização

def novo_espectro(titulo, piso_db):
    fig, ax = plt.subplots(figsize=FIGSIZE, constrained_layout=True)
    fig.canvas.manager.set_window_title(titulo.split("—")[0].strip())
    ax.set_title(titulo, fontsize=12)
    ax.set_xlim(0, F_MAX / 1e6)
    ax.set_ylim(piso_db, 0)
    ax.set_xlabel("Frequência [MHz]")
    ax.set_ylabel("Magnitude [dB]")
    ax.grid(True, alpha=0.3)
    return fig, ax


figuras = {}

# Fig. 1 - Mixer ideal ----------------------------------------------------
fig1, ax1 = novo_espectro(
    "Fig. 1 — Misturador ideal: multiplicação pura, apenas "
    r"$|f_{LO}-f_{RF}|$ e $f_{LO}+f_{RF}$", -80)
ax1.plot(freq_ideal / 1e6, mag_ideal, color="0.78", lw=0.9)
colorir_raias(ax1, raias_ideal, -80)
anotar(ax1, raias_ideal, sep_mhz=0)
ax1.text(0.98, 0.04,
         f"{len(raias_ideal)} raias acima de −60 dB\n"
         "nenhum harmônico, nenhuma intermodulação, nenhum vazamento",
         transform=ax1.transAxes, fontsize=9, ha="right", va="bottom",
         bbox=CAIXA)
figuras["fig1_mixer_ideal"] = fig1

# Fig. 2 - Mixer real: a Fig. 4 do artigo, anotada ------------------------
fig2, ax2 = novo_espectro(
    r"Fig. 2 — Misturador real: família de espúrios $m\,f_{RF} \pm n\,f_{LO}$",
    -80)
ax2.plot(freq_real / 1e6, mag_real, color="0.78", lw=0.9)
colorir_raias(ax2, raias_real, -80)
anotar(ax2, raias_real)
for cor, texto in [(COR_UTIL, "útil: IF e harmônicos  (m = |n|)"),
                   (COR_VAZAMENTO, "vazamento / harmônico puro  (m = 0 ou n = 0)"),
                   (COR_IMD, "intermodulação  (m, n ≠ 0)")]:
    ax2.plot([], [], "s", ms=6, color=cor, label=texto)
ax2.legend(loc="lower right", fontsize=8.5, framealpha=0.92)
ax2.text(0.015, 0.04,
         f"{len(raias_real)} raias identificadas acima de −75 dB  "
         f"(as {MAX_ROTULOS} mais fortes estão rotuladas;\n"
         "a lista completa sai no terminal)\n"
         f"SFDR ≈ {sfdr_real:.0f} dBc — limitado pelo vazamento de LO",
         transform=ax2.transAxes, fontsize=9, va="bottom", bbox=CAIXA)
figuras["fig2_mixer_real"] = fig2

# Fig. 3 - Mixer digital --------------------------------------------------
fig3, ax3 = novo_espectro(
    f"Fig. 3 — Misturador digital (FPGA): DDS {ACC_BITS}/{ADDR_BITS}/{LUT_BITS} "
    f"bits, produto em {OUT_BITS} bits", -150)
ax3.plot(freq_dig / 1e6, mag_dig, color=COR_DIGITAL, lw=1.0)
ax3.set_ylim(-150, 20)
for fu, nome in [(f_IF, "IF"), (f_RF + f_LO, "soma")]:
    ax3.annotate(f"{nome}  ({fu/1e6:.0f} MHz)", xy=(fu / 1e6, -5),
                 xytext=(fu / 1e6 + 22, 8), fontsize=9, color=COR_UTIL,
                 arrowprops=dict(arrowstyle="->", color=COR_UTIL, lw=0.9))
ax3.axhline(-6.02 * ADDR_BITS, color="0.45", ls="--", lw=1)
ax3.text(F_MAX / 1e6 * 0.5, -6.02 * ADDR_BITS + 3,
         f"teoria do truncamento de fase:  −6,02 × {ADDR_BITS} bits = "
         f"−{6.02*ADDR_BITS:.0f} dBc",
         fontsize=8.5, color="0.3", va="bottom", ha="center")
ax3.text(0.98, 0.04,
         f"SFDR medido ≈ {sfdr_dig:.0f} dBc\n"
         f"contra ≈ {sfdr_real:.0f} dBc do diodo (Fig. 2)\n"
         "as raias restantes vêm da aritmética finita,\n"
         "não da física do semicondutor",
         transform=ax3.transAxes, fontsize=9, ha="right", va="bottom",
         bbox=CAIXA)
figuras["fig3_mixer_digital"] = fig3

# Fig. 4 - Atraso de grupo ------------------------------------------------
fig4, ax4 = plt.subplots(figsize=FIGSIZE, constrained_layout=True)
fig4.canvas.manager.set_window_title("Fig. 4 - Atraso de grupo")
ax4.plot(w_el / (2 * np.pi) / 1e6, tau_el * 1e9, color=COR_REAL, lw=1.6,
         label=f"Elíptico analógico, ordem {ORDEM_ELIP} "
               f"({ATENUACAO:.0f} dB @ {F_PARA/1e6:.0f} MHz)")
ax4.plot(w_fir / 1e6, tau_fir * 1e9, color=COR_DIGITAL, lw=1.6,
         label=f"FIR de fase linear, {n_taps} taps @ {fs_dec/1e6:.0f} MHz "
               f"(após CIC R={R_CIC})")
ax4.axhline(tau_fir_teorico * 1e9, color=COR_DIGITAL, ls=":", lw=1.2,
            label=r"$\tau_g = (N-1)/2 \cdot T_s$"
                  f" = {tau_fir_teorico*1e9:.0f} ns, constante")
ax4.axvline(f_IF / 1e6, color="0.45", ls="--", lw=1)
ax4.annotate(f"IF = {f_IF/1e6:.0f} MHz", xy=(f_IF / 1e6, tau_el_if * 1e9),
             xytext=(f_IF / 1e6 - 12, tau_el_if * 1e9 + 28), fontsize=9,
             color="0.25",
             arrowprops=dict(arrowstyle="->", color="0.45", lw=0.9))
ax4.annotate(f"pico: {tau_el.max()*1e9:.0f} ns\n"
             f"({tau_el.max()/tau_el_if:.1f}× o valor na IF)",
             xy=(w_el[np.argmax(tau_el)] / (2 * np.pi) / 1e6,
                 tau_el.max() * 1e9),
             xytext=(62, tau_el.max() * 1e9 * 0.62), fontsize=9, color=COR_REAL,
             arrowprops=dict(arrowstyle="->", color=COR_REAL, lw=0.9))

ax4.set_title("Fig. 4 — O custo da filtragem: atraso de grupo, "
              "roll-off abrupto × fase linear", fontsize=12)
ax4.set_xlabel("Frequência [MHz]")
ax4.set_ylabel(r"Atraso de grupo  $\tau_g$  [ns]")
ax4.set_xlim(0, 150)
ax4.set_ylim(0, max(tau_el.max(), tau_fir_teorico) * 1e9 * 1.6)
ax4.grid(True, alpha=0.3)
ax4.legend(loc="upper right", fontsize=9, framealpha=0.92)
ax4.text(0.015, 0.96,
         f"Na IF:   elíptico {tau_el_if*1e9:.0f} ns   |   "
         f"CIC + FIR {(tau_cic + tau_fir_teorico)*1e9:.0f} ns\n"
         "O caminho digital não é mais rápido: é plano e previsível.\n"
         "O elíptico varia dentro da própria banda e deforma o envelope.",
         transform=ax4.transAxes, fontsize=9, va="top", bbox=CAIXA)
figuras["fig4_atraso_de_grupo"] = fig4


# ------------------------------------------------------------------ saída

tabela(raias_real, "Espúrios do misturador real (Cenário B):")
print(f"\nSFDR  diodo   ≈ {sfdr_real:6.1f} dBc")
print(f"SFDR  digital ≈ {sfdr_dig:6.1f} dBc   "
      f"(teoria: {-6.02*ADDR_BITS:.1f} dBc)")
print(f"\nAtraso de grupo na IF:")
print(f"  elíptico analógico : {tau_el_if*1e9:6.1f} ns  "
      f"(pico {tau_el.max()*1e9:.1f} ns)")
print(f"  CIC (R={R_CIC}, {N_CIC} est.) : {tau_cic*1e9:6.1f} ns")
print(f"  FIR ({n_taps} taps)      : {tau_fir_teorico*1e9:6.1f} ns")
print(f"  total digital      : {(tau_cic + tau_fir_teorico)*1e9:6.1f} ns")

if "--salvar" in sys.argv:
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figuras")
    os.makedirs(destino, exist_ok=True)
    for nome, fig in figuras.items():
        caminho = os.path.join(destino, f"{nome}.png")
        fig.savefig(caminho, dpi=150)
        print(f"salvo: {caminho}")
else:
    plt.show()
