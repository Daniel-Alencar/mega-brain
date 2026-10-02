#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
 DETECÇÃO I/Q PARA LLRF DE ACELERADORES
   Cenário 1 - Desmodulação analógica direta (homódina / Zero-IF)  [Fig. 5(b)]
   Cenário 2 - Amostragem digital via IF + DDC na FPGA             [Fig. 5(c)]
==============================================================================

Escala de frequências
---------------------
Simular uma portadora de 500 MHz em "tempo contínuo" exigiria uma grade de
vários GHz. Usamos f_RF = 50 MHz (fator 1/10): os produtos de mistura, a
diafonia, o aliasing e o jitter seguem exatamente a mesma física, só os
números absolutos mudam de escala. O efeito do jitter também é extrapolado
para os 500 MHz reais.

Modelo do sinal
---------------
    s_RF(t) = A(t)·cos(ω_RF·t + φ(t))
            = I(t)·cos(ω_RF·t) − Q(t)·sin(ω_RF·t)
    I(t) = A(t)·cos φ(t),   Q(t) = A(t)·sin φ(t),   z(t) = I + jQ = A·e^{jφ}

Cenário 1 - Demodulador I/Q analógico imperfeito
-------------------------------------------------
Os dois LOs deveriam estar em quadratura (90°), mas estão separados por
90° + Δθ, e o ramo Q tem ganho (1 + ε). Dividindo o erro de fase de forma
simétrica (±Δθ/2):

    LO_I(t) =  2·cos(ω t − Δθ/2)
    LO_Q(t) = −2·(1+ε)·sin(ω t + Δθ/2)

Após a mistura e o passa-baixas (que elimina os termos em 2ω):

    ⎡I'⎤   ⎡    cos(Δθ/2)        −sin(Δθ/2)    ⎤ ⎡I⎤   ⎡DC_I⎤
    ⎣Q'⎦ = ⎣ −(1+ε)·sin(Δθ/2)  (1+ε)·cos(Δθ/2) ⎦ ⎣Q⎦ + ⎣DC_Q⎦
                              M

  * Os termos fora da diagonal são a DIAFONIA (cross-talk): Q vaza para o
    canal I e I vaza para o canal Q, na razão tan(Δθ/2) (≈ −27 dB p/ Δθ = 5°).
  * Em notação complexa, z' = α·z + β·z*. O termo-imagem β·z* transforma o
    círculo |z| = cte em uma ELIPSE inclinada. A razão de rejeição de imagem é
        IRR = |α|²/|β|² = (1 + g² + 2g·cos Δθ) / (1 + g² − 2g·cos Δθ), g = 1+ε.
  * M não é uma rotação (não é ortogonal; det M = (1+ε)·cos Δθ), por isso não
    se corrige com uma calibração escalar de ganho/fase: é preciso uma matriz
    2×2 inversa, que deriva com temperatura, frequência e nível de potência.

Cenário 2 - IF + ADC + DDC
--------------------------
Um ÚNICO mixer leva o RF para f_IF = f_RF − f_LO. Como há um só caminho
analógico, qualquer erro de ganho/fase dele é COMUM a I e Q: equivale a uma
rotação + escala do vetor z, trivialmente calibrável. A separação I/Q é feita
na FPGA pela multiplicação por cos/sin numéricos, ortogonais por construção
(90,000°). Com f_s = 4·f_IF, as amostras sucessivas valem I, −Q, −I, +Q, ...

Uso:  python3 iq_analog_vs_ddc.py            (mostra a figura e salva PNG)
      python3 iq_analog_vs_ddc.py --no-show  (apenas salva PNG)
"""

import argparse
from dataclasses import dataclass, replace

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.interpolate import CubicSpline


# =============================================================================
# 0. PARÂMETROS DA SIMULAÇÃO
# =============================================================================
@dataclass(frozen=True)
class Parametros:
    # --- Escala de frequências ----------------------------------------------
    f_rf: float = 50e6            # portadora RF (500 MHz reais / 10)
    f_if: float = 20e6            # frequência intermediária
    fs_adc: float = 80e6          # f_s = 4·f_IF -> amostragem I/Q síncrona
    sobreamostragem: int = 16     # grade "analógica": fs_sim = 16·f_s = 1,28 GHz
    duracao: float = 20e-6        # janela simulada [s]

    # --- Envelope de teste A(t), φ(t) ----------------------------------------
    a_ini: float = 0.3            # amplitude antes do degrau
    a_fim: float = 1.0            # amplitude depois do degrau
    t_degrau: float = 2.5e-6      # centro do degrau suave (tanh)
    tau_degrau: float = 0.3e-6    # "suavidade" do degrau
    t_rampa: tuple = (5e-6, 17e-6)  # rampa de fase: início e fim
    giro_fase: float = 2 * np.pi  # excursão total de fase (uma volta: 0 -> 360°)
    m_am: float = 0.01            # AM residual de 1% (gera USB/LSB visíveis)
    f_am: float = 1e6             # frequência da AM residual
    snr_rf_db: float = 60.0       # SNR do RF na banda inteira da simulação
    banda_rf: tuple = (40e6, 62.5e6)  # passa-banda do front-end (centro geom. = 50 MHz)

    # --- Cenário 1: imperfeições do demodulador analógico --------------------
    erro_quad_graus: float = 5.0        # Δθ: LOs a 95° em vez de 90°
    desbal_ganho: float = 0.05          # ε: ganho (1+ε) no ramo Q
    offset_dc: tuple = (0.010, -0.015)  # vazamento do LO / auto-mistura -> DC
    fc_lpf_analog: float = 5e6
    ordem_lpf_analog: int = 4

    # --- Cenário 2: heteródino + ADC + DDC -----------------------------------
    fc_aa: float = 35e6           # anti-aliasing (Nyquist do ADC = 40 MHz)
    ordem_aa: int = 8
    jitter_rms: float = 5e-12     # jitter do clock do ADC [s rms]
    bits_adc: int = 14
    fundo_escala: float = 1.25    # faixa do ADC: ±FS
    fir_taps: int = 129
    fc_fir: float = 4e6

    # --- Análise ---------------------------------------------------------------
    margem_borda: float = 1e-6    # descarta transientes de borda dos filtros no MSE
    semente: int = 2024

    @property
    def fs_sim(self):
        return self.sobreamostragem * self.fs_adc

    @property
    def f_lo_het(self):
        # LO abaixo do RF (low-side): preserva o sentido da fase na IF
        return self.f_rf - self.f_if


# Paleta (identidade fixa por método em todos os painéis)
COR_REAL = "#0b0b0b"      # ground truth
COR_ANALOG = "#eb6834"    # cenário 1 (analógico)
COR_DIGITAL = "#2a78d6"   # cenário 2 (DDC)
COR_ADC = "#1baf7a"       # amostras do ADC
COR_AUX = "#52514e"       # respostas de filtro, marcações
AZUIS = ["#9cc3f0", "#5b9be6", "#2a78d6", "#103d7a"]  # rampa sequencial (jitter)


# =============================================================================
# 1. SINAL DE ENTRADA (CAVIDADE RF)
# =============================================================================
def envelope(t, p):
    """Envelope complexo de teste: degrau suave de amplitude + rampa de fase."""
    a = p.a_ini + (p.a_fim - p.a_ini) * 0.5 * (1 + np.tanh((t - p.t_degrau) / p.tau_degrau))
    a = a * (1 + p.m_am * np.sin(2 * np.pi * p.f_am * t))
    t0, t1 = p.t_rampa
    x = np.clip((t - t0) / (t1 - t0), 0.0, 1.0)
    fase = p.giro_fase * 0.5 * (1 - np.cos(np.pi * x))   # rampa com derivada contínua
    return a, fase


def iq_verdadeiro(t, p):
    a, fase = envelope(t, p)
    return a * np.cos(fase), a * np.sin(fase)


def gerar_sinal_rf(p, rng):
    """s_RF(t) = A(t)·cos(ω_RF t + φ(t)) + ruído, numa grade quase contínua."""
    t = np.arange(round(p.duracao * p.fs_sim)) / p.fs_sim
    a, fase = envelope(t, p)
    i, q = a * np.cos(fase), a * np.sin(fase)
    w = 2 * np.pi * p.f_rf
    rf_limpo = i * np.cos(w * t) - q * np.sin(w * t)       # = A·cos(ωt + φ)

    ruido_rms = np.sqrt(0.5 * p.a_fim**2 / 10 ** (p.snr_rf_db / 10))
    rf = rf_limpo + rng.normal(0.0, ruido_rms, t.size)
    # Front-end de RF (pickup da cavidade + filtro de banda): limita o ruído
    # e elimina a frequência-imagem antes de qualquer mixer.
    sos_rf = signal.butter(3, p.banda_rf, btype="bandpass", fs=p.fs_sim, output="sos")
    rf = signal.sosfiltfilt(sos_rf, rf)
    return dict(t=t, a=a, fase=fase, i=i, q=q, rf=rf)


# =============================================================================
# 2. CENÁRIO 1 - DEMODULADOR I/Q ANALÓGICO (HOMÓDINO / ZERO-IF)
# =============================================================================
def matriz_diafonia(p):
    """Matriz M que relaciona [I', Q'] medidos com [I, Q] verdadeiros."""
    h = np.deg2rad(p.erro_quad_graus) / 2
    g = 1 + p.desbal_ganho
    return np.array([[np.cos(h), -np.sin(h)],
                     [-g * np.sin(h), g * np.cos(h)]])


def coeficientes_imagem(m):
    """z' = α·z + β·z*  ->  retorna (α, β) a partir de M = [[a, b], [c, d]]."""
    (a, b), (c, d) = m
    alfa = 0.5 * ((a + d) + 1j * (c - b))
    beta = 0.5 * ((a - d) + 1j * (c + b))
    return alfa, beta


def demodulador_analogico(sinal, p):
    t, rf = sinal["t"], sinal["rf"]
    w = 2 * np.pi * p.f_rf
    d = np.deg2rad(p.erro_quad_graus)
    g = 1 + p.desbal_ganho

    # Divisor de potência -> dois mixers com LOs imperfeitos (separação 90° + Δθ)
    lo_i = 2 * np.cos(w * t - d / 2)
    lo_q = -2 * g * np.sin(w * t + d / 2)
    mix_i = rf * lo_i      # contém banda base + produto em 2·f_RF
    mix_q = rf * lo_q

    # Passa-baixas analógico (Butterworth). sosfiltfilt = fase zero: remove o
    # atraso de grupo (constante e calibrável num sistema real), de modo que o
    # erro medido venha só das imperfeições do hardware. Como o filtro é
    # aplicado duas vezes, a resposta efetiva é |H(f)|².
    sos = signal.butter(p.ordem_lpf_analog, p.fc_lpf_analog, fs=p.fs_sim, output="sos")
    i = signal.sosfiltfilt(sos, mix_i) + p.offset_dc[0]
    q = signal.sosfiltfilt(sos, mix_q) + p.offset_dc[1]
    return dict(t=t, mix_i=mix_i, mix_q=mix_q, i=i, q=q, sos=sos)


# =============================================================================
# 3. CENÁRIO 2 - HETERÓDINO PARA IF + ADC + DDC (FPGA)
# =============================================================================
def receptor_ddc(sinal, p, rng):
    t, rf = sinal["t"], sinal["rf"]

    # (a) Down-conversion analógica com um único LO puro: RF -> IF
    lo = 2 * np.cos(2 * np.pi * p.f_lo_het * t)
    mix = rf * lo          # IF = f_RF − f_LO  e  soma = f_RF + f_LO

    # (b) Anti-aliasing: a soma f_RF + f_LO = 80 MHz = f_s cairia em DC!
    sos_aa = signal.butter(p.ordem_aa, p.fc_aa, fs=p.fs_sim, output="sos")
    x_if = signal.sosfiltfilt(sos_aa, mix)

    # (c) ADC: amostra o sinal "contínuo" nos instantes reais (com jitter)
    n = np.arange(round(p.duracao * p.fs_adc))
    t_n = n / p.fs_adc
    t_real = t_n + rng.normal(0.0, p.jitter_rms, n.size)
    x_adc = CubicSpline(t, x_if)(t_real)
    lsb = 2 * p.fundo_escala / 2**p.bits_adc
    x_adc = np.clip(np.round(x_adc / lsb) * lsb, -p.fundo_escala, p.fundo_escala - lsb)

    # (d) NCO na FPGA: cos/sin numéricos exatamente ortogonais. A FPGA usa os
    #     instantes ideais n/f_s: não tem como saber o jitter.
    nco_cos = 2 * np.cos(2 * np.pi * p.f_if * t_n)
    nco_sin = -2 * np.sin(2 * np.pi * p.f_if * t_n)
    prod_i = x_adc * nco_cos
    prod_q = x_adc * nco_sin

    # (e) FIR passa-baixas (fase linear) + compensação do atraso (N−1)/2
    h = signal.firwin(p.fir_taps, p.fc_fir, fs=p.fs_adc, window=("kaiser", 8.0))
    atraso = (p.fir_taps - 1) // 2
    i = np.full(n.size, np.nan)
    q = np.full(n.size, np.nan)
    i[:-atraso] = signal.lfilter(h, 1.0, prod_i)[atraso:]
    q[:-atraso] = signal.lfilter(h, 1.0, prod_q)[atraso:]

    # (f) Calibração ESCALAR do caminho analógico único (ganho do AA na IF).
    #     Vale igualmente para I e Q: não há descasamento entre canais.
    _, h_aa_if = signal.sosfreqz(sos_aa, worN=[p.f_if], fs=p.fs_sim)
    ganho_cal = np.abs(h_aa_if[0]) ** 2    # |H|² por causa do sosfiltfilt
    i /= ganho_cal
    q /= ganho_cal

    return dict(mix=mix, x_if=x_if, t_n=t_n, t_real=t_real, x_adc=x_adc,
                nco_cos=nco_cos, prod_i=prod_i, i=i, q=q,
                sos_aa=sos_aa, h_fir=h, ganho_cal=ganho_cal)


# =============================================================================
# 4. JITTER: ERRO DE AMOSTRAGEM EM IF vs EM RF
# =============================================================================
def analise_jitter(p, rng, n=200_000):
    """Erro de amostragem e(t) ≈ s'(t)·Δt  ->  e_rms = 2π·f·σ_j·A/√2.

    O erro cresce com a frequência do sinal amostrado, não com f_s: amostrar
    em IF (20 MHz) é muito menos sensível do que amostrar diretamente o RF.
    """
    t_n = np.arange(n) / p.fs_adc
    dt = rng.normal(0.0, p.jitter_rms, n)
    casos = [("IF", p.f_if), ("RF simulado", p.f_rf), ("RF real (500 MHz)", 500e6)]
    resultado = []
    for rotulo, f in casos:
        fase0 = rng.uniform(0, 2 * np.pi)
        e = np.sin(2 * np.pi * f * (t_n + dt) + fase0) - np.sin(2 * np.pi * f * t_n + fase0)
        e_rms = np.sqrt(np.mean(e**2))
        snr_sim = 20 * np.log10((1 / np.sqrt(2)) / e_rms)
        snr_teo = -20 * np.log10(2 * np.pi * f * p.jitter_rms)
        resultado.append(dict(rotulo=rotulo, f=f, e_rms=e_rms, snr_sim=snr_sim, snr_teo=snr_teo))
    return resultado


# =============================================================================
# 5. MÉTRICAS
# =============================================================================
def metricas(t, i_est, q_est, p):
    i0, q0 = iq_verdadeiro(t, p)
    m = (t >= p.margem_borda) & (t <= p.duracao - p.margem_borda) & np.isfinite(i_est)
    e_i, e_q = i_est[m] - i0[m], q_est[m] - q0[m]
    z0, z = i0[m] + 1j * q0[m], i_est[m] + 1j * q_est[m]
    erro_amp = (np.abs(z) - np.abs(z0)) / np.abs(z0) * 100
    erro_fase = np.rad2deg(np.angle(z * np.conj(z0)))
    return dict(mse_i=np.mean(e_i**2), mse_q=np.mean(e_q**2),
                mse_iq=np.mean(e_i**2 + e_q**2),
                amp_rms=np.sqrt(np.mean(erro_amp**2)), amp_max=np.max(np.abs(erro_amp)),
                fase_rms=np.sqrt(np.mean(erro_fase**2)), fase_max=np.max(np.abs(erro_fase)))


def erros_no_tempo(t, i_est, q_est, p):
    i0, q0 = iq_verdadeiro(t, p)
    z0, z = i0 + 1j * q0, i_est + 1j * q_est
    erro_amp = (np.abs(z) - np.abs(z0)) / np.abs(z0) * 100
    erro_fase = np.rad2deg(np.angle(z * np.conj(z0)))
    return erro_amp, erro_fase


def espectro_db(x, fs):
    """Espectro de amplitude unilateral (janela Hann), em dB rel. a amplitude 1."""
    x = x[np.isfinite(x)]
    w = np.hanning(x.size)
    mag = np.abs(np.fft.rfft(x * w)) * 2 / np.sum(w)
    return np.fft.rfftfreq(x.size, 1 / fs), 20 * np.log10(mag + 1e-12)


# =============================================================================
# 6. RELATÓRIO NO TERMINAL
# =============================================================================
def db(x):
    return 10 * np.log10(x)


def imprimir_relatorio(p, sinal, ddc, met_a, met_d, contribs, jit):
    m = matriz_diafonia(p)
    alfa, beta = coeficientes_imagem(m)
    irr = abs(alfa) ** 2 / abs(beta) ** 2
    g = 1 + p.desbal_ganho
    irr_formula = (1 + g**2 + 2 * g * np.cos(np.deg2rad(p.erro_quad_graus))) / \
                  (1 + g**2 - 2 * g * np.cos(np.deg2rad(p.erro_quad_graus)))
    linha = "=" * 78

    print(linha)
    print(" DETECÇÃO I/Q: DEMODULAÇÃO ANALÓGICA (ZERO-IF) vs AMOSTRAGEM DIGITAL (IF + DDC)")
    print(linha)
    print(f" f_RF = {p.f_rf/1e6:.0f} MHz (escala 1/10 de 500 MHz) | f_LO,het = {p.f_lo_het/1e6:.0f} MHz"
          f" | f_IF = {p.f_if/1e6:.0f} MHz | f_s = {p.fs_adc/1e6:.0f} MSPS")
    print(f" Grade 'analógica': {p.fs_sim/1e9:.2f} GHz, {sinal['t'].size} pontos, "
          f"janela de {p.duracao*1e6:.0f} µs (MSE avaliado em [{p.margem_borda*1e6:.0f}, "
          f"{(p.duracao-p.margem_borda)*1e6:.0f}] µs)")

    print("\n[1] DIAFONIA NO DEMODULADOR ANALÓGICO")
    print(f"    Δθ = {p.erro_quad_graus:.1f}° (LOs a {90+p.erro_quad_graus:.0f}°),  ε = {p.desbal_ganho:.2f},"
          f"  DC = ({p.offset_dc[0]:+.3f}, {p.offset_dc[1]:+.3f})")
    print("    [I']   [ cos(Δθ/2)        −sin(Δθ/2)      ] [I]")
    print("    [Q'] = [ −(1+ε)sin(Δθ/2)   (1+ε)cos(Δθ/2) ] [Q] + DC")
    print(f"    M = [[{m[0,0]:+.4f}, {m[0,1]:+.4f}],")
    print(f"         [{m[1,0]:+.4f}, {m[1,1]:+.4f}]]")
    print(f"    Fuga Q→I: |M12/M11| = {abs(m[0,1]/m[0,0]):.4f} ({20*np.log10(abs(m[0,1]/m[0,0])):.1f} dB)")
    print(f"    Fuga I→Q: |M21/M22| = {abs(m[1,0]/m[1,1]):.4f} ({20*np.log10(abs(m[1,0]/m[1,1])):.1f} dB)")
    print(f"    z' = α·z + β·z*:  α = {alfa:.4f},  β = {beta:.4f}")
    print(f"    IRR = |α/β|² = {irr:.1f} ({db(irr):.1f} dB)  [fórmula fechada: {db(irr_formula):.1f} dB]")

    print("\n[2] ERRO QUADRÁTICO MÉDIO DE RECONSTRUÇÃO (vs. ground truth)")
    print(f"    {'Método':<22}{'MSE_I':>12}{'MSE_Q':>12}{'MSE_IQ':>12}{'|ΔA| rms':>11}{'Δφ rms':>10}")
    for nome, mm in [("Analógico (Zero-IF)", met_a), ("Digital (IF + DDC)", met_d)]:
        print(f"    {nome:<22}{mm['mse_i']:>12.3e}{mm['mse_q']:>12.3e}{mm['mse_iq']:>12.3e}"
              f"{mm['amp_rms']:>10.3f}%{mm['fase_rms']:>9.4f}°")
    print(f"    -> Ganho de fidelidade do DDC: {db(met_a['mse_iq']/met_d['mse_iq']):.1f} dB em MSE_IQ")
    print(f"    -> Erros de pico: analógico {met_a['amp_max']:.2f}% / {met_a['fase_max']:.2f}°;"
          f"  digital {met_d['amp_max']:.4f}% / {met_d['fase_max']:.4f}°")

    print("\n    Contribuição isolada de cada imperfeição analógica (MSE_IQ):")
    for nome, mm in contribs:
        print(f"      {nome:<28}{mm['mse_iq']:>12.3e}")
    print("    (O MSE residual do DDC vem de ruído térmico, quantização e jitter -\n"
          "     nenhum termo de descasamento entre canais.)")

    print("\n[3] DDC NA FPGA (f_s = 4·f_IF)")
    print(f"    NCO cos[n]: {np.array2string(np.round(ddc['nco_cos'][:8]/2, 12) + 0.0, precision=0)}"
          "  -> amostras = I, −Q, −I, +Q, ...")
    print(f"    FIR: {p.fir_taps} taps, fc = {p.fc_fir/1e6:.0f} MHz, atraso compensado = "
          f"{(p.fir_taps-1)//2} amostras ({(p.fir_taps-1)/2/p.fs_adc*1e6:.2f} µs)")
    print(f"    Calibração escalar do AA na IF (comum a I e Q): 1/{ddc['ganho_cal']:.6f}")
    print(f"    ADC: {p.bits_adc} bits, ±{p.fundo_escala} FS, jitter σ_j = {p.jitter_rms*1e12:.1f} ps")

    print(f"\n[4] JITTER DO CLOCK (σ_j = {p.jitter_rms*1e12:.1f} ps): SNR limite = −20·log10(2π·f·σ_j)")
    print(f"    {'Sinal amostrado':<22}{'f':>10}{'e_rms':>12}{'SNR sim.':>11}{'SNR teor.':>11}")
    for r in jit:
        print(f"    {r['rotulo']:<22}{r['f']/1e6:>7.0f} MHz{r['e_rms']:>12.2e}"
              f"{r['snr_sim']:>9.1f} dB{r['snr_teo']:>9.1f} dB")
    print(f"    -> Amostrar em IF em vez de 500 MHz ganha 20·log10(500/{p.f_if/1e6:.0f}) = "
          f"{20*np.log10(500e6/p.f_if):.1f} dB de imunidade ao jitter.")
    print(linha)


# =============================================================================
# 7. VISUALIZAÇÃO
# =============================================================================
def estilizar(ax, titulo, xlabel, ylabel):
    ax.set_title(titulo, loc="left", fontsize=11, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25, lw=0.6)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)


def caixa(ax, texto, x=0.02, y=0.97, va="top", ha="left", fonte=8.5, mono=False):
    ax.text(x, y, texto, transform=ax.transAxes, va=va, ha=ha, fontsize=fonte,
            family="monospace" if mono else None,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#c3c2b7", alpha=0.92))


def sombrear_bordas(ax, p):
    ax.axvspan(0, p.margem_borda * 1e6, color="#e8e8e6", zorder=0)
    ax.axvspan((p.duracao - p.margem_borda) * 1e6, p.duracao * 1e6, color="#e8e8e6", zorder=0)


def plotar(p, sinal, ana, ddc, met_a, met_d, jit):
    t, t_us = sinal["t"], sinal["t"] * 1e6
    tn_us = ddc["t_n"] * 1e6
    m_mat = matriz_diafonia(p)
    alfa, beta = coeficientes_imagem(m_mat)
    irr_db = db(abs(alfa) ** 2 / abs(beta) ** 2)

    fig = plt.figure(figsize=(22, 28), layout="constrained")
    gs = fig.add_gridspec(5, 6, height_ratios=[1, 1.1, 1, 0.8, 1.35])
    fig.suptitle("Detecção I/Q em LLRF: demodulação analógica Zero-IF (Fig. 5b) × amostragem "
                 "digital IF + DDC (Fig. 5c)\n"
                 f"f_RF = {p.f_rf/1e6:.0f} MHz (escala 1/10 de 500 MHz) · f_IF = {p.f_if/1e6:.0f} MHz"
                 f" · f_s = {p.fs_adc/1e6:.0f} MSPS · Δθ = {p.erro_quad_graus:.0f}° · "
                 f"ε = {p.desbal_ganho:.0%} · σ_jitter = {p.jitter_rms*1e12:.0f} ps",
                 fontsize=15, fontweight="bold")

    # ------------------------------------------------------------------ Painel 1a
    ax = fig.add_subplot(gs[0, 0:3])
    ax.plot(t_us, sinal["rf"], color=COR_AUX, lw=0.3, alpha=0.7, label="RF modulado s(t)")
    ax.plot(t_us, sinal["a"], color=COR_REAL, lw=1.6, label="Envelope ±A(t)")
    ax.plot(t_us, -sinal["a"], color=COR_REAL, lw=1.6)
    t_zoom = (7.70e-6, 7.85e-6)
    ax.axvspan(t_zoom[0] * 1e6, t_zoom[1] * 1e6, color=COR_DIGITAL, alpha=0.25, label="Janela do zoom →")
    ax.annotate("degrau suave\nde amplitude", xy=(p.t_degrau * 1e6, 0.65), xytext=(0.6, 1.3),
                fontsize=9, arrowprops=dict(arrowstyle="->", color=COR_AUX))
    ax.annotate("", xy=(p.t_rampa[1] * 1e6, 1.25), xytext=(p.t_rampa[0] * 1e6, 1.25),
                arrowprops=dict(arrowstyle="<->", color=COR_AUX))
    ax.text(np.mean(p.t_rampa) * 1e6, 1.3, f"rampa de fase φ: 0° → 360° (A constante + AM residual de {p.m_am:.0%})",
            ha="center", va="bottom", fontsize=9)
    ax.set_ylim(-1.5, 1.6)
    ax.set_xlim(0, p.duracao * 1e6)
    estilizar(ax, "Painel 1a · Sinal de RF da cavidade (janela completa)", "Tempo [µs]", "Amplitude [u.a.]")
    ax.legend(loc="lower right", fontsize=8.5, ncol=3)

    # ------------------------------------------------------------------ Painel 1b
    ax = fig.add_subplot(gs[0, 3:6])
    mz = (t >= t_zoom[0]) & (t <= t_zoom[1])
    ax.plot(t_us[mz], sinal["rf"][mz], color=COR_AUX, lw=1.0,
            label=f"RF ({p.f_rf/1e6:.0f} MHz)")
    ax.plot(t_us[mz], ddc["x_if"][mz], color=COR_DIGITAL, lw=2.0,
            label=f"IF após mixer + anti-aliasing ({p.f_if/1e6:.0f} MHz)")
    mn = (ddc["t_n"] >= t_zoom[0]) & (ddc["t_n"] <= t_zoom[1])
    ax.vlines(ddc["t_real"][mn] * 1e6, 0, ddc["x_adc"][mn], color=COR_ADC, lw=1.2)
    ax.plot(ddc["t_real"][mn] * 1e6, ddc["x_adc"][mn], "o", ms=8, color=COR_ADC, mec="white", mew=1.5,
            label=f"Amostras do ADC ({p.fs_adc/1e6:.0f} MSPS, {p.bits_adc} bits, σ_j = {p.jitter_rms*1e12:.0f} ps)")
    nomes = {0: "I", 1: "−Q", 2: "−I", 3: "+Q"}
    for k in np.flatnonzero(mn):
        y = ddc["x_adc"][k]
        ax.annotate(nomes[k % 4], (ddc["t_real"][k] * 1e6, y), textcoords="offset points",
                    xytext=(0, 9 if y >= 0 else -16), ha="center", fontsize=9, fontweight="bold")
    ax.axhline(0, color=COR_AUX, lw=0.6)
    ax.set_ylim(-1.45, 1.45)
    estilizar(ax, "Painel 1b · Zoom: RF → IF → amostragem síncrona (f_s = 4·f_IF)",
              "Tempo [µs]", "Amplitude [u.a.]")
    ax.legend(loc="lower left", fontsize=8.5)
    caixa(ax, "Com f_s = 4·f_IF, a fase do NCO avança 90° por amostra:\n"
              "x[n] = I·cos(πn/2) − Q·sin(πn/2) → I, −Q, −I, +Q, ...\n"
              "A quadratura é definida pelo RELÓGIO, não por hardware.",
          x=0.99, y=0.97, ha="right")

    # ------------------------------------------------------------------ Painel 2a
    ax = fig.add_subplot(gs[1, 0:2])
    f, s_rf = espectro_db(sinal["rf"], p.fs_sim)
    _, s_mix = espectro_db(ana["mix_i"], p.fs_sim)
    _, s_out = espectro_db(ana["i"], p.fs_sim)
    _, h_lpf = signal.sosfreqz(ana["sos"], worN=f, fs=p.fs_sim)
    fm = f / 1e6
    ax.plot(fm, s_mix, color=COR_ANALOG, lw=0.8, alpha=0.4, label="Saída do mixer I (antes do LPF)")
    ax.plot(fm, s_rf, color=COR_REAL, lw=0.8, label="RF de entrada")
    ax.plot(fm, s_out, color=COR_ANALOG, lw=1.6, label="I'(t) após LPF")
    ax.plot(fm, 40 * np.log10(np.abs(h_lpf) + 1e-12), "--", color=COR_AUX, lw=1.2,
            label=f"|H_LPF|² Butterworth {p.ordem_lpf_analog}ª ordem, {p.fc_lpf_analog/1e6:.0f} MHz")
    ax.annotate("banda base\n(I, Q em DC)", xy=(1, -5), xytext=(8, 2), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=COR_AUX))
    ax.annotate("RF", xy=(p.f_rf / 1e6, -5), xytext=(p.f_rf / 1e6 - 12, 2), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=COR_AUX))
    ax.annotate("2·f_RF (soma)\nremovido pelo LPF", xy=(2 * p.f_rf / 1e6, -8),
                xytext=(2 * p.f_rf / 1e6 - 30, 2), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=COR_AUX))
    ax.set_xlim(0, 120)
    ax.set_ylim(-130, 12)
    estilizar(ax, "Painel 2a · Espectro: via analógica Zero-IF", "Frequência [MHz]", "Magnitude [dB]")
    ax.legend(loc="lower left", fontsize=8)
    # Inset: bandas laterais em torno da portadora
    ins = ax.inset_axes([0.52, 0.42, 0.45, 0.33])
    mi = (fm > p.f_rf / 1e6 - 2.5) & (fm < p.f_rf / 1e6 + 2.5)
    ins.plot(fm[mi], s_rf[mi], color=COR_REAL, lw=1.0)
    for df, nome in [(-1, "LSB"), (0, "f_c"), (1, "USB")]:
        fx = p.f_rf / 1e6 + df * p.f_am / 1e6
        ins.annotate(nome, (fx, s_rf[np.argmin(np.abs(fm - fx))]), textcoords="offset points",
                     xytext=(0, 4), ha="center", fontsize=8, fontweight="bold")
    ins.set_ylim(-110, 10)
    ins.set_title("Zoom em f_RF: bandas laterais da AM de 1 MHz", fontsize=8)
    ins.tick_params(labelsize=7)
    ins.grid(True, alpha=0.25)

    # ------------------------------------------------------------------ Painel 2b
    ax = fig.add_subplot(gs[1, 2:4])
    _, s_mixh = espectro_db(ddc["mix"], p.fs_sim)
    _, s_if = espectro_db(ddc["x_if"], p.fs_sim)
    _, h_aa = signal.sosfreqz(ddc["sos_aa"], worN=f, fs=p.fs_sim)
    ax.plot(fm, s_mixh, color=COR_DIGITAL, lw=0.8, alpha=0.4, label="Saída do mixer heteródino")
    ax.plot(fm, s_rf, color=COR_REAL, lw=0.8, label="RF de entrada")
    ax.plot(fm, s_if, color=COR_DIGITAL, lw=1.6, label="IF após anti-aliasing (entrada do ADC)")
    ax.plot(fm, 40 * np.log10(np.abs(h_aa) + 1e-12), "--", color=COR_AUX, lw=1.2,
            label=f"|H_AA|² Butterworth {p.ordem_aa}ª ordem, {p.fc_aa/1e6:.0f} MHz")
    ax.axvline(p.fs_adc / 2e6, color=COR_ADC, lw=1.5, ls=":")
    ax.text(p.fs_adc / 2e6 + 1, -45, "Nyquist\ndo ADC\n(f_s/2)", fontsize=8.5)
    ax.axvline(p.f_lo_het / 1e6, color=COR_AUX, lw=1.0, ls=":")
    ax.text(p.f_lo_het / 1e6 + 1, -30, "f_LO", fontsize=8.5)
    ax.annotate("IF = f_RF − f_LO", xy=(p.f_if / 1e6, -5), xytext=(2, 4), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=COR_AUX))
    ax.annotate("f_RF + f_LO = f_s\n→ cairia em DC (alias)!", xy=((p.f_rf + p.f_lo_het) / 1e6, -6),
                xytext=(80, 2), fontsize=9, ha="center",
                arrowprops=dict(arrowstyle="->", color=COR_AUX))
    ax.set_xlim(0, 120)
    ax.set_ylim(-130, 12)
    estilizar(ax, "Painel 2b · Espectro: down-conversion RF → IF (analógico)",
              "Frequência [MHz]", "Magnitude [dB]")
    ax.legend(loc="lower right", fontsize=8)

    # ------------------------------------------------------------------ Painel 2c
    ax = fig.add_subplot(gs[1, 4:6])
    fd, s_adc = espectro_db(ddc["x_adc"], p.fs_adc)
    _, s_prod = espectro_db(ddc["prod_i"], p.fs_adc)
    fd2, s_id = espectro_db(ddc["i"], p.fs_adc)
    w_fir, h_fir = signal.freqz(ddc["h_fir"], worN=2048, fs=p.fs_adc)
    ax.plot(fd / 1e6, s_prod, color=COR_DIGITAL, lw=0.8, alpha=0.4, label="x[n]·2cos(Ω_IF n) (NCO)")
    ax.plot(fd / 1e6, s_adc, color=COR_ADC, lw=1.0, label="Amostras do ADC x[n]")
    ax.plot(fd2 / 1e6, s_id, color=COR_DIGITAL, lw=1.6, label="I[n] após FIR")
    ax.plot(w_fir / 1e6, 20 * np.log10(np.abs(h_fir) + 1e-12), "--", color=COR_AUX, lw=1.2,
            label=f"|H_FIR| ({p.fir_taps} taps, Kaiser, {p.fc_fir/1e6:.0f} MHz)")
    ax.annotate("I(t) em DC", xy=(0.5, -5), xytext=(4, 4), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=COR_AUX))
    ax.annotate("IF", xy=(p.f_if / 1e6, -5), xytext=(p.f_if / 1e6 + 3, 4), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=COR_AUX))
    ax.annotate("2·f_IF = f_s/2\nremovido pelo FIR", xy=(2 * p.f_if / 1e6 - 0.3, -8),
                xytext=(27, -40), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=COR_AUX))
    ax.set_xlim(0, p.fs_adc / 2e6)
    ax.set_ylim(-130, 12)
    estilizar(ax, "Painel 2c · Espectro digital (FPGA): IF → banda base",
              "Frequência [MHz]  (0 … f_s/2)", "Magnitude [dB]")
    ax.legend(loc="lower left", fontsize=8)

    # ------------------------------------------------------------------ Painel 3a/3b
    i_mod = m_mat[0, 0] * sinal["i"] + m_mat[0, 1] * sinal["q"] + p.offset_dc[0]
    q_mod = m_mat[1, 0] * sinal["i"] + m_mat[1, 1] * sinal["q"] + p.offset_dc[1]
    for col, (nome, verd, est_a, est_d, mod) in enumerate([
            ("I(t)", sinal["i"], ana["i"], ddc["i"], i_mod),
            ("Q(t)", sinal["q"], ana["q"], ddc["q"], q_mod)]):
        ax = fig.add_subplot(gs[2, 3 * col:3 * col + 3])
        sombrear_bordas(ax, p)
        ax.plot(t_us, verd, color=COR_REAL, lw=2.4, label=f"{nome} original (ground truth)")
        ax.plot(t_us, est_a, color=COR_ANALOG, lw=1.5, label=f"{nome} analógico (Δθ, ε, DC)")
        ax.plot(t_us, mod, ":", color=COR_REAL, lw=1.0, label="Modelo teórico M·[I, Q]ᵀ + DC")
        ax.plot(tn_us, est_d, "--", color=COR_DIGITAL, lw=1.6, label=f"{nome} digital (IF + DDC)")
        ax.set_xlim(0, p.duracao * 1e6)
        estilizar(ax, f"Painel 3{'ab'[col]} · Recuperação de {nome}", "Tempo [µs]", f"{nome} [u.a.]")
        ax.legend(loc="lower left", fontsize=8.5)

        if nome == "Q(t)":
            # Antes da rampa Q = 0: o que aparece no canal Q analógico é I vazando
            tx = 4.0e-6
            k = np.argmin(np.abs(t - tx))
            ax.annotate(f"Fuga I → Q: Q' = −(1+ε)·sin(Δθ/2)·I + DC_Q\n"
                        f"≈ {ana['q'][k]:+.3f} com Q = 0",
                        xy=(tx * 1e6, ana["q"][k]), xytext=(1.0, 0.55), fontsize=9,
                        arrowprops=dict(arrowstyle="->", color=COR_ANALOG))
        else:
            # Em φ = 90° temos I = 0: o que aparece no canal I analógico é Q vazando
            k = np.argmin(np.abs(sinal["fase"] - np.pi / 2) + (t < p.t_rampa[0]) * 10)
            ax.annotate(f"Fuga Q → I: I' = −sin(Δθ/2)·Q + DC_I\n"
                        f"≈ {ana['i'][k]:+.3f} com I = 0 (φ = 90°)",
                        xy=(t_us[k], ana["i"][k]), xytext=(t_us[k] + 1.2, 0.55), fontsize=9,
                        arrowprops=dict(arrowstyle="->", color=COR_ANALOG))
        caixa(ax, f"MSE_{nome[0]} analógico = {met_a['mse_' + nome[0].lower()]:.2e}\n"
                  f"MSE_{nome[0]} digital     = {met_d['mse_' + nome[0].lower()]:.2e}",
              x=0.99, y=0.03, va="bottom", ha="right", mono=True)

    # ------------------------------------------------------------------ Painel 3c/3d
    ea_amp, ea_fase = erros_no_tempo(t, ana["i"], ana["q"], p)
    ed_amp, ed_fase = erros_no_tempo(ddc["t_n"], ddc["i"], ddc["q"], p)
    m_a = (t >= p.margem_borda) & (t <= p.duracao - p.margem_borda)
    m_d = (ddc["t_n"] >= p.margem_borda) & (ddc["t_n"] <= p.duracao - p.margem_borda)
    for col, (nome, ea, ed, unid, chave) in enumerate([
            ("amplitude ΔA/A", ea_amp, ed_amp, "%", "amp"),
            ("fase Δφ", ea_fase, ed_fase, "°", "fase")]):
        ax = fig.add_subplot(gs[3, 3 * col:3 * col + 3])
        sombrear_bordas(ax, p)
        ax.axhline(0, color=COR_AUX, lw=0.6)
        ax.plot(t_us[m_a], ea[m_a], color=COR_ANALOG, lw=1.5, label="Analógico")
        ax.plot(tn_us[m_d], ed[m_d], color=COR_DIGITAL, lw=1.5, label="Digital DDC")
        ax.set_xlim(0, p.duracao * 1e6)
        estilizar(ax, f"Painel 3{'cd'[col]} · Erro de {nome} (grandeza que o LLRF regula)",
                  "Tempo [µs]", f"Erro [{unid}]")
        ax.legend(loc="upper left", fontsize=8.5)
        caixa(ax, f"rms analógico = {met_a[chave + '_rms']:.3f}{unid}\n"
                  f"rms digital   = {met_d[chave + '_rms']:.4f}{unid}\n"
                  "Durante a rampa o erro analógico oscila\n"
                  "com 2φ: assinatura do termo-imagem β·z*",
              x=0.99, y=0.97, ha="right", mono=False)

    # ------------------------------------------------------------------ Painel 4
    ax = fig.add_subplot(gs[4, 0:3])
    th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(th), np.sin(th), ":", color=COR_AUX, lw=1.0, label="Círculo unitário (|z| = 1)")
    ax.plot(sinal["i"][m_a], sinal["q"][m_a], color=COR_REAL, lw=2.4, label="Trajetória real z = I + jQ")
    ax.plot(ana["i"][m_a], ana["q"][m_a], color=COR_ANALOG, lw=1.5,
            label="Analógico: elipse inclinada + offset")
    ax.plot(ddc["i"][m_d], ddc["q"][m_d], "--", color=COR_DIGITAL, lw=1.6, label="Digital DDC")
    # Erro analógico ampliado 5× para tornar a distorção elíptica evidente
    amp = 5
    ax.plot(sinal["i"][m_a] + amp * (ana["i"][m_a] - sinal["i"][m_a]),
            sinal["q"][m_a] + amp * (ana["q"][m_a] - sinal["q"][m_a]),
            ":", color=COR_ANALOG, lw=1.6, label=f"Analógico com erro ampliado {amp}× (visualização)")
    ax.plot(*p.offset_dc, "x", color=COR_ANALOG, ms=10, mew=2)
    ax.annotate("offset DC\n(vazamento do LO)", xy=p.offset_dc, xytext=(0.12, -0.3), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=COR_ANALOG))
    ax.annotate("degrau de A\n(φ = 0)", xy=(0.6, 0.0), xytext=(0.45, 0.3), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=COR_AUX))
    ax.axhline(0, color=COR_AUX, lw=0.6)
    ax.axvline(0, color=COR_AUX, lw=0.6)
    ax.set_aspect("equal")
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(-1.65, 1.5)
    estilizar(ax, "Painel 4 · Plano complexo (constelação I × Q)", "I [u.a.]", "Q [u.a.]")
    ax.legend(loc="lower left", fontsize=8.5)
    caixa(ax, f"M = [{m_mat[0,0]:+.4f}  {m_mat[0,1]:+.4f}]\n"
              f"    [{m_mat[1,0]:+.4f}  {m_mat[1,1]:+.4f}]\n\n"
              f"z' = α·z + β·z*\n"
              f"|α| = {abs(alfa):.4f}\n"
              f"|β| = {abs(beta):.4f}\n"
              f"IRR = |α/β|² = {irr_db:.1f} dB\n\n"
              f"DDC: M = 1 (ortogonal\nexato, IRR → ∞)",
          x=0.99, y=0.97, ha="right", mono=True, fonte=9)

    # ------------------------------------------------------------------ Painel 5
    ax = fig.add_subplot(gs[4, 3:6])
    fv = np.logspace(6, np.log10(2e9), 300)
    for cor, sig in zip(AZUIS, [0.1e-12, 1e-12, p.jitter_rms, 10e-12]):
        destaque = np.isclose(sig, p.jitter_rms, rtol=1e-6, atol=0.0)
        ax.plot(fv, -20 * np.log10(2 * np.pi * fv * sig), color=COR_REAL if destaque else cor,
                lw=2.2 if destaque else 1.4, ls="--" if destaque else "-",
                label=f"σ_j = {sig*1e12:g} ps" + (" (simulado)" if destaque else ""))
    for r in jit:
        ax.plot(r["f"], r["snr_sim"], "o", ms=9, color=COR_ADC, mec=COR_REAL, mew=1.2, zorder=5)
        ax.annotate(f"{r['rotulo']}\n{r['snr_sim']:.1f} dB", (r["f"], r["snr_sim"]),
                    textcoords="offset points", xytext=(8, 6), fontsize=8.5)
    ax.plot([], [], "o", ms=9, color=COR_ADC, mec=COR_REAL, label="Simulação Monte Carlo")
    snr_if = -20 * np.log10(2 * np.pi * p.f_if * p.jitter_rms)
    snr_rf = -20 * np.log10(2 * np.pi * 500e6 * p.jitter_rms)
    ax.annotate("", xy=(500e6, snr_rf), xytext=(500e6, snr_if),
                arrowprops=dict(arrowstyle="<->", color=COR_REAL, lw=1.4))
    ax.text(560e6, (snr_if + snr_rf) / 2, f"{snr_if - snr_rf:.0f} dB\nde vantagem\nem IF",
            fontsize=9, va="center")
    ax.axvline(p.f_if, color=COR_AUX, lw=0.8, ls=":")
    ax.axvline(500e6, color=COR_AUX, lw=0.8, ls=":")
    ax.set_xscale("log")
    ax.set_xlim(1e6, 2e9)
    ax.set_ylim(20, 125)
    estilizar(ax, "Painel 5 · Sensibilidade ao jitter do clock: amostrar em IF × em RF",
              "Frequência do sinal amostrado [Hz]", "SNR limitada por jitter [dB]")
    ax.legend(loc="lower left", fontsize=8.5)
    caixa(ax, "e(t) ≈ s'(t)·Δt  ⇒  SNR = −20·log10(2π·f·σ_j)\n"
              "O erro depende da frequência do sinal,\nnão da taxa de amostragem.",
          x=0.99, y=0.97, ha="right")

    return fig


# =============================================================================
# 8. PROGRAMA PRINCIPAL
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Demodulação I/Q analógica vs. IF + DDC")
    parser.add_argument("--no-show", action="store_true", help="não abre a janela, só salva o PNG")
    parser.add_argument("--saida", default="iq_analog_vs_ddc.png", help="arquivo da figura")
    args = parser.parse_args()

    p = Parametros()
    rng = np.random.default_rng(p.semente)

    sinal = gerar_sinal_rf(p, rng)
    ana = demodulador_analogico(sinal, p)
    ddc = receptor_ddc(sinal, p, rng)
    jit = analise_jitter(p, rng)

    met_a = metricas(sinal["t"], ana["i"], ana["q"], p)
    met_d = metricas(ddc["t_n"], ddc["i"], ddc["q"], p)

    # Liga uma imperfeição por vez para separar as contribuições ao MSE
    sem_erros = replace(p, erro_quad_graus=0.0, desbal_ganho=0.0, offset_dc=(0.0, 0.0))
    contribs = []
    for nome, pp in [("Só Δθ (quadratura)", replace(sem_erros, erro_quad_graus=p.erro_quad_graus)),
                     ("Só ε (desbalanço de ganho)", replace(sem_erros, desbal_ganho=p.desbal_ganho)),
                     ("Só offset DC", replace(sem_erros, offset_dc=p.offset_dc)),
                     ("Nenhuma (hardware ideal)", sem_erros)]:
        r = demodulador_analogico(sinal, pp)
        contribs.append((nome, metricas(sinal["t"], r["i"], r["q"], p)))

    imprimir_relatorio(p, sinal, ddc, met_a, met_d, contribs, jit)

    fig = plotar(p, sinal, ana, ddc, met_a, met_d, jit)
    fig.savefig(args.saida, dpi=110)
    print(f"Figura salva em: {args.saida}")
    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
