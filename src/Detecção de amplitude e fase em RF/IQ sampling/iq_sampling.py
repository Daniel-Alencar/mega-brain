# -*- coding: utf-8 -*-
"""
IQ sampling: amplitude e fase de uma IF com um único ADC
========================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/Detecção de amplitude e fase em RF/IQ sampling/iq_sampling.py" IQSampling   # rascunho
    manim -pqh "src/Detecção de amplitude e fase em RF/IQ sampling/iq_sampling.py" IQSampling   # final

Requer LaTeX (MathTex).

Roteiro (segue "docs/Detecção de amplitude e fase em RF/IQ sampling"):
    Abertura
    Cena 1 - Representação polar × cartesiana: y = A·sin(ωt + φ0) = I·sin ωt + Q·cos ωt
    Cena 2 - O que o ADC mede: só a projeção vertical do fasor, um número por amostra
    Cena 3 - Amostragem síncrona f_s = 4·f_IF: amostras Q, I, −Q, −I
    Cena 4 - Algoritmo de rotação: matrizes com 0 e ±1, sem multiplicadores
    Cena 5 - Generalização f_s = m·f_IF: sensibilidade ao ruído ∝ 1/|sin Δφ|
    Cena 6 - Limitações: offset DC (ondulação em f_IF) e aliasing de harmônicas
    Resumo

Convenção:
    y(t) = A·sin(ωt + φ0) = I·sin(ωt) + Q·cos(ωt),  I = A·cos φ0,  Q = A·sin φ0
    Cada amostra é a projeção vertical do fasor de ângulo ωt + φ0.
"""

import numpy as np
from manim import *

# Paleta didática (fixa em todas as cenas)
COR_RF = BLUE            # fasor / sinal de IF
COR_I = GOLD             # componente I
COR_Q = GREEN            # componente Q
COR_AMOSTRA = WHITE      # amostras do ADC
COR_ERRO = RED           # erros, ruído, harmônicas sobre a portadora
COR_ERRO2 = ORANGE       # valor estimado com erro
COR_DIGITAL = TEAL       # processamento digital
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}
FI0 = np.deg2rad(35)                      # fase φ0 usada nas cenas
I0, Q0 = np.cos(FI0), np.sin(FI0)         # A = 1
ALTURAS = [0, 1.0, 0.55, 0.5, 0.42, 0.36, 0.3, 0.26]   # amplitudes das harmônicas (ilustrativas)


# =============================================================================
# Utilitários de construção
# =============================================================================
def P(x, y):
    return np.array([x, y, 0.0])


def tex(s, cor=WHITE, tamanho=34):
    return MathTex(s, color=cor, font_size=tamanho)


def tex_partes(partes, tamanho=34):
    """Fórmula multicolorida. partes = [(tex, cor), ...]; cada tex deve ser LaTeX balanceado."""
    m = MathTex(*[p[0] for p in partes], font_size=tamanho)
    for sub, p in zip(m, partes):
        sub.set_color(p[1])
    return m


def seta(a, b, cor, largura=6):
    if np.linalg.norm(b - a) < 1e-3:
        return VMobject()
    return Arrow(a, b, buff=0, color=cor, stroke_width=largura,
                 max_tip_length_to_length_ratio=0.18, max_stroke_width_to_length_ratio=12)


def segmento(a, b, cor, largura=6):
    if np.linalg.norm(b - a) < 1e-3:
        return VMobject()
    return Line(a, b, color=cor, stroke_width=largura)


def tracejada(a, b, cor, largura=3):
    if np.linalg.norm(b - a) < 0.05:
        return VMobject()
    return DashedLine(a, b, color=cor, stroke_width=largura, dash_length=0.08)


def arco_angulo(centro, raio, inicio, angulo, cor, largura=3):
    if abs(angulo) < 0.02:
        return VMobject()
    return Arc(radius=raio, start_angle=inicio, angle=angulo, arc_center=centro,
               color=cor, stroke_width=largura)


def plano(centro, tam=5.6, alcance=1.4):
    eixos = Axes(x_range=[-alcance, alcance, 0.5], y_range=[-alcance, alcance, 0.5],
                 x_length=tam, y_length=tam,
                 axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO})
    eixos.move_to(centro)
    rot_i = Text("I", font_size=30, color=COR_I).next_to(eixos.x_axis.get_end(), DOWN, buff=0.15)
    rot_q = Text("Q", font_size=30, color=COR_Q).next_to(eixos.y_axis.get_end(), LEFT, buff=0.15)
    return eixos, VGroup(rot_i, rot_q)


def eixos_tempo(centro, largura, altura, x_range, y_range):
    return Axes(x_range=x_range, y_range=y_range, x_length=largura, y_length=altura,
                axis_config=EIXO_CFG).move_to(centro)


def rotulo_eixo(ax, mob):
    """Coloca um rótulo acima do canto esquerdo de um eixo."""
    return mob.next_to(ax, UP, buff=0.04).align_to(ax, LEFT)


def marcar_x(ax, valores, rotulos, tamanho=18):
    return VGroup(*[Text(r, font_size=tamanho, color=COR_EIXO).next_to(ax.c2p(v, 0), DOWN, buff=0.12)
                    for v, r in zip(valores, rotulos)])


def haste(ax, x, y, cor, raio=0.06, largura=2):
    return VGroup(Line(ax.c2p(x, 0), ax.c2p(x, y), color=cor, stroke_width=largura),
                  Dot(ax.c2p(x, y), radius=raio, color=cor))


def raia(ax, f, altura, cor, largura=6):
    """Raia espectral (seta vertical) em f."""
    return seta(ax.c2p(f, 0), ax.c2p(f, altura), cor, largura)


def alias(f, fs):
    """Frequência aparente de f depois da amostragem a fs (rebatida para [0, fs/2])."""
    f = f % fs
    return fs - f if f > fs / 2 else f


def posicoes_alias(fs, kmax=7):
    """Posição na tela de cada harmônica depois do aliasing (afasta as que caem juntas)."""
    grupos = {}
    for k in range(1, kmax + 1):
        grupos.setdefault(round(alias(k, fs), 6), []).append(k)
    pos = {}
    for a, ks in grupos.items():
        if 1 in ks:   # a fundamental fica parada; as outras se alternam ao redor
            desloc = [0, 0.09, -0.09, 0.18, -0.18]
            for j, k in enumerate(ks):
                pos[k] = a + desloc[j]
        else:
            for j, k in enumerate(ks):
                pos[k] = a + 0.09 * (j - (len(ks) - 1) / 2)
    return pos, grupos


# =============================================================================
# Cena
# =============================================================================
class IQSampling(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_polar()
        self.cena_adc()
        self.cena_sincrona()
        self.cena_rotacao()
        self.cena_generalizacao()
        self.cena_offset()
        self.cena_harmonicas()
        self.cena_resumo()

    # ------------------------------------------------------------- utilidades
    def titulo_cena(self, texto):
        t = Text(texto, font_size=32, weight=BOLD).to_corner(UL, buff=0.35)
        linha = Line(t.get_corner(DL), t.get_corner(DR), color=COR_EIXO,
                     stroke_width=2).shift(DOWN * 0.12)
        self.play(Write(t), Create(linha), run_time=1)
        return VGroup(t, linha)

    def trocar_titulo(self, titulo, texto):
        novo = Text(texto, font_size=32, weight=BOLD).to_corner(UL, buff=0.35)
        linha = Line(novo.get_corner(DL), novo.get_corner(DR), color=COR_EIXO,
                     stroke_width=2).shift(DOWN * 0.12)
        self.play(Transform(titulo[0], novo), Transform(titulo[1], linha), run_time=0.8)

    def legenda(self, texto, anterior=None, cor=GREY_A):
        nova = Text(texto, font_size=24, color=cor).to_edge(DOWN, buff=0.3)
        if anterior is None:
            self.play(FadeIn(nova, shift=UP * 0.2), run_time=0.7)
        else:
            self.play(FadeOut(anterior, shift=UP * 0.2), FadeIn(nova, shift=UP * 0.2), run_time=0.7)
        return nova

    def limpar(self):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        self.wait(0.2)

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("IQ sampling", font_size=60, weight=BOLD)
        sub = Text("Amplitude e fase de uma IF com um único ADC", font_size=30, color=GREY_A)
        seq = tex_partes([(r"Q,\ ", COR_Q), (r"I,\ ", COR_I), (r"-Q,\ ", COR_Q), (r"-I,\ ", COR_I),
                          (r"\dots", WHITE)], 36)
        g = VGroup(titulo, sub, seq).arrange(DOWN, buff=0.35)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(seq, shift=UP * 0.2))
        self.wait(1.2)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_polar(self):
        self.titulo_cena("1 · Representação polar × cartesiana")
        e1 = tex(r"y(t) = A\sin(\omega t + \varphi_0)", WHITE, 38).move_to(P(-3.5, 2.5))
        e_id = tex(r"\sin(\alpha+\beta) = \sin\alpha\cos\beta + \cos\alpha\sin\beta", GREY_A, 28
                   ).move_to(P(-3.5, 1.65))
        e2 = tex_partes([(r"y(t) = ", WHITE), (r"\underbrace{A\cos\varphi_0}_{I}", COR_I),
                         (r"\sin\omega t + ", WHITE), (r"\underbrace{A\sin\varphi_0}_{Q}", COR_Q),
                         (r"\cos\omega t", WHITE)], 34).move_to(P(-3.5, 2.3))
        e3 = tex_partes([(r"y(t) = ", WHITE), (r"I", COR_I), (r"\sin\omega t + ", WHITE),
                         (r"Q", COR_Q), (r"\cos\omega t", WHITE)], 38).move_to(P(-3.5, 2.5))
        defs = VGroup(tex(r"I = A\cos\varphi_0", COR_I, 32), tex(r"Q = A\sin\varphi_0", COR_Q, 32)
                      ).arrange(RIGHT, buff=0.8).move_to(P(-3.5, 1.55))
        inv = VGroup(tex(r"A = \sqrt{I^2 + Q^2}", COR_RF, 32),
                     tex(r"\varphi_0 = \operatorname{atan}(Q/I)", WHITE, 32)
                     ).arrange(RIGHT, buff=0.7).move_to(P(-3.5, 0.6))

        eixos, rotulos = plano(P(3.6, -0.3), 4.8, 1.3)
        o = eixos.c2p(0, 0)
        ponta = eixos.c2p(I0, Q0)
        fasor = seta(o, ponta, COR_RF, 7)
        rot_a = tex(r"A", COR_RF, 30).move_to((o + ponta) / 2 + 0.3 * np.array([-np.sin(FI0), np.cos(FI0), 0]))
        arco = arco_angulo(o, 0.55, 0, FI0, WHITE, 2)
        rot_fi = tex(r"\varphi_0", WHITE, 28).move_to(o + 0.85 * np.array([np.cos(FI0 / 2), np.sin(FI0 / 2), 0]))
        seg_i = segmento(o, eixos.c2p(I0, 0), COR_I, 9)
        seg_q = segmento(o, eixos.c2p(0, Q0), COR_Q, 9)
        proj = VGroup(tracejada(ponta, eixos.c2p(I0, 0), COR_I), tracejada(ponta, eixos.c2p(0, Q0), COR_Q))

        leg = self.legenda("Qualquer sinal senoidal de RF ou IF tem amplitude A e fase φ0")
        self.play(Write(e1))
        self.play(Create(eixos), FadeIn(rotulos))
        self.play(GrowArrow(fasor), FadeIn(rot_a), Create(arco), FadeIn(rot_fi))
        leg = self.legenda("Expandindo com a identidade da soma de arcos", leg)
        self.play(FadeIn(e_id, shift=UP * 0.2))
        self.play(ReplacementTransform(e1, e2), FadeOut(e_id), run_time=1.5)
        leg = self.legenda("Os coeficientes de sin ωt e cos ωt são as componentes I e Q", leg)
        self.play(TransformFromCopy(e2[1], defs[0]), TransformFromCopy(e2[3], defs[1]), run_time=1.3)
        self.play(ReplacementTransform(e2, e3))
        self.play(Create(proj), Create(seg_i), Create(seg_q))
        leg = self.legenda("I e Q são as projeções do fasor nos eixos (coordenadas cartesianas)", leg)
        self.play(Indicate(seg_i, color=COR_I), Indicate(seg_q, color=COR_Q))
        leg = self.legenda("A volta para polar: Pitágoras e arco-tangente", leg)
        self.play(Write(inv), run_time=1.5)

        porque = VGroup(
            Text("Por que trabalhar com I e Q?", font_size=24, weight=BOLD),
            Text("✗  √ e atan a cada amostra: caros em hardware e lentos", font_size=18, color=COR_ERRO),
            Text("✓  controle PI e rotações de fase são lineares em I e Q", font_size=18, color=COR_I),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(P(-3.6, -1.5))
        caixa = SurroundingRectangle(porque, color=COR_EIXO, buff=0.2, corner_radius=0.1)
        leg = self.legenda("No digital, fica-se em I e Q sempre que possível", leg)
        self.play(Create(caixa), FadeIn(porque[0]))
        self.play(FadeIn(porque[1], shift=RIGHT * 0.2))
        self.play(FadeIn(porque[2], shift=RIGHT * 0.2))
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 2
    def cena_adc(self):
        self.titulo_cena("2 · O que um ADC consegue medir")
        eixos, rotulos = plano(P(-4.4, -0.3), 3.6, 1.3)
        o = eixos.c2p(0, 0)
        circulo = DashedVMobject(Circle(radius=eixos.c2p(1, 0)[0] - o[0], color=COR_EIXO).move_to(o),
                                 num_dashes=40).set_stroke(width=2)
        ax = eixos_tempo(P(2.3, -0.3), 7.4, 3.6, [0, 2, 0.25], [-1.3, 1.3, 0.5])
        rot_ax = rotulo_eixo(ax, tex(r"y(t) = A\sin(\omega t + \varphi_0)", COR_RF, 28))
        rot_t = Text("tempo (períodos) →", font_size=18, color=COR_EIXO).next_to(ax, DOWN, buff=0.05
                                                                                  ).align_to(ax, RIGHT)
        t = ValueTracker(0.0)

        def ang():
            return TAU * t.get_value() + FI0

        def ponta():
            return eixos.c2p(np.cos(ang()), np.sin(ang()))

        fasor = always_redraw(lambda: seta(o, ponta(), COR_RF, 6))
        proj = always_redraw(lambda: tracejada(ponta(), ax.c2p(t.get_value(), np.sin(ang())), GREY_A, 2))
        onda = always_redraw(lambda: ax.plot(lambda x: np.sin(TAU * x + FI0),
                                             x_range=[0, max(t.get_value(), 0.01), 0.01],
                                             color=COR_RF, stroke_width=4))
        cursor = always_redraw(lambda: Dot(ax.c2p(t.get_value(), np.sin(ang())), radius=0.07, color=WHITE))

        leg = self.legenda("O sinal é a projeção vertical de um fasor girando")
        self.play(Create(eixos), FadeIn(rotulos), Create(circulo), Create(ax), FadeIn(rot_ax), FadeIn(rot_t))
        self.add(fasor, proj, onda, cursor)
        self.play(t.animate.set_value(2), run_time=6, rate_func=linear)

        xs = np.arange(11) * 0.2
        amostras = VGroup(*[haste(ax, x, np.sin(TAU * x + FI0), COR_AMOSTRA) for x in xs])
        leg = self.legenda("O ADC só lê essa altura: UM número por amostra", leg)
        self.play(LaggedStart(*[GrowFromPoint(a, ax.c2p(x, 0)) for a, x in zip(amostras, xs)],
                              lag_ratio=0.15), run_time=2)
        self.wait(0.5)

        # Uma amostra não define o vetor
        self.play(FadeOut(amostras), t.animate.set_value(0), run_time=1.5)
        for m in (fasor, proj, onda, cursor):
            m.clear_updaters()
        y0 = np.sin(FI0)
        reta_q = DashedLine(eixos.c2p(-1.3, y0), eixos.c2p(1.3, y0), color=COR_Q, stroke_width=3)
        candidatos = VGroup(*[seta(o, eixos.c2p(x, y0), GREY_B, 3).set_opacity(0.6) for x in (-1.1, -0.45, 0.35, 1.2)])
        leg = self.legenda("Uma amostra só diz a altura: qualquer fasor com a ponta nesta reta serve", leg, COR_Q)
        self.play(Create(reta_q))
        self.play(LaggedStart(*[GrowArrow(c) for c in candidatos], lag_ratio=0.2))
        self.wait(0.6)
        reta_i = DashedLine(eixos.c2p(I0, -1.3), eixos.c2p(I0, 1.3), color=COR_I, stroke_width=3)
        leg = self.legenda("Uma segunda amostra, ¼ de período depois, mede a outra projeção", leg, COR_I)
        self.play(Create(reta_i), FadeOut(candidatos))
        alvo = Dot(eixos.c2p(I0, Q0), radius=0.1, color=WHITE)
        self.play(GrowFromCenter(alvo), Indicate(fasor, color=WHITE))
        leg = self.legenda("Correlacionando amostras consecutivas, reconstruímos o vetor (I, Q)", leg)
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 3
    def cena_sincrona(self):
        self.titulo_cena("3 · Amostragem síncrona: f_s = 4·f_IF")
        formula = tex(r"\Delta\phi = \omega T_s = 2\pi f_{IF}\cdot\frac{1}{4 f_{IF}} = \frac{\pi}{2} = 90^\circ",
                      WHITE, 30).move_to(P(3.3, 2.55))
        eixos, rotulos = plano(P(-4.4, -0.4), 3.4, 1.3)
        o = eixos.c2p(0, 0)
        ax = eixos_tempo(P(2.3, -0.4), 7.4, 3.4, [0, 2, 0.25], [-1.3, 1.3, 0.5])
        rot_t = Text("tempo (períodos de IF) →", font_size=18, color=COR_EIXO).next_to(ax, DOWN, buff=0.05
                                                                                        ).align_to(ax, RIGHT)
        onda = ax.plot(lambda x: np.sin(TAU * x + FI0), x_range=[0, 2, 0.01], color=COR_RF,
                       stroke_width=3).set_stroke(opacity=0.45)
        k_val = ValueTracker(0.0)

        def ang():
            return FI0 + k_val.get_value() * PI / 2

        def ponta():
            return eixos.c2p(np.cos(ang()), np.sin(ang()))

        fasor = always_redraw(lambda: seta(o, ponta(), COR_RF, 6))
        proj = always_redraw(lambda: tracejada(ponta(), ax.c2p(k_val.get_value() / 4, np.sin(ang())), GREY_A, 2))

        nomes = [(r"Q", COR_Q), (r"I", COR_I), (r"-Q", COR_Q), (r"-I", COR_I)]
        avaliacoes = [
            "ωt₀ = 0:  y = I·sin 0 + Q·cos 0 = Q",
            "ωt₁ = π/2:  y = I·sin(π/2) + Q·cos(π/2) = I",
            "ωt₂ = π:  y = I·sin π + Q·cos π = −Q",
            "ωt₃ = 3π/2:  y = I·sin(3π/2) + Q·cos(3π/2) = −I",
        ]
        partes = []
        for k in range(8):
            nome, cor = nomes[k % 4]
            partes.append((nome + r",\ ", cor))
        partes.append((r"\dots", WHITE))
        fluxo = tex_partes(partes, 34).move_to(P(0, -2.75))
        rot_fluxo = Text("saída do ADC:", font_size=20, color=GREY_A).next_to(fluxo, LEFT, buff=0.3)

        leg = self.legenda("Amostrando 4 vezes por período, o fasor avança exatamente 90° entre amostras")
        self.play(Write(formula), run_time=1.5)
        self.play(Create(eixos), FadeIn(rotulos), Create(ax), FadeIn(rot_t), Create(onda))
        self.add(fasor, proj)
        self.play(FadeIn(rot_fluxo))

        for k in range(9):
            if k > 0:
                self.play(k_val.animate.set_value(k), run_time=0.7 if k < 4 else 0.4)
            nome, cor = nomes[k % 4]
            y = np.sin(FI0 + k * PI / 2)
            h = haste(ax, k / 4, y, cor, 0.08, 3)
            r = tex(nome, cor, 30).next_to(ax.c2p(k / 4, y), UP if y >= 0 else DOWN, buff=0.12)
            anims = [GrowFromPoint(h, ax.c2p(k / 4, 0)), FadeIn(r)]
            if k < 8:
                anims.append(FadeIn(fluxo[k]))
            self.play(*anims, run_time=0.6 if k < 4 else 0.35)
            if k < 4:
                leg = self.legenda(avaliacoes[k], leg, cor)
                self.wait(0.6)
        self.play(FadeIn(fluxo[8]))
        leg = self.legenda("O ADC entrega um padrão cíclico: Q, I, −Q, −I, …", leg)
        self.play(Indicate(fluxo, scale_factor=1.08))
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 4
    def cena_rotacao(self):
        self.titulo_cena("4 · Algoritmo de rotação")
        nomes = [(r"Q", COR_Q), (r"I", COR_I), (r"-Q", COR_Q), (r"-I", COR_I)]
        caixas = VGroup()
        for k in range(8):
            nome, cor = nomes[k % 4]
            q = Square(side_length=0.8, color=COR_EIXO, stroke_width=2)
            v = tex(nome, cor, 32).move_to(q)
            idx = tex(rf"y_{k}", GREY_B, 22).next_to(q, DOWN, buff=0.1)
            caixas.add(VGroup(q, v, idx).move_to(P(-6.0 + 1.1 * k, 2.25)))
        geral = tex(r"\begin{pmatrix} I \\ Q \end{pmatrix}_{t_i} = "
                    r"\begin{pmatrix} \cos\Delta\phi_i & -\sin\Delta\phi_i \\ \sin\Delta\phi_i & \cos\Delta\phi_i \end{pmatrix}"
                    r"\begin{pmatrix} y_{i+1} \\ y_i \end{pmatrix}", WHITE, 30).move_to(P(-3.0, 0.55))
        passos = Text("Δφᵢ ∈ {0°, −90°, −180°, −270°}", font_size=20, color=GREY_A).next_to(geral, DOWN, buff=0.2)

        casos = {0: ("0^\\circ", "1 & 0 \\\\ 0 & 1", "I \\\\ Q"),
                 1: ("-90^\\circ", "0 & 1 \\\\ -1 & 0", "-Q \\\\ I"),
                 2: ("-180^\\circ", "-1 & 0 \\\\ 0 & -1", "-I \\\\ -Q"),
                 3: ("-270^\\circ", "0 & -1 \\\\ 1 & 0", "Q \\\\ -I")}

        def especifica(i):
            ang, mat, vet = casos[i % 4]
            return tex_partes([
                (rf"\Delta\phi_{{{i}}} = {ang}:\quad", GREY_A),
                (rf"\begin{{pmatrix}} {mat} \end{{pmatrix}}", COR_DIGITAL),
                (rf"\begin{{pmatrix}} {vet} \end{{pmatrix}}", WHITE),
                (r"=", WHITE),
                (r"\begin{pmatrix} I \\ Q \end{pmatrix}", COR_RF),
            ], 32).move_to(P(-3.0, -1.35))

        eixos, rotulos = plano(P(4.3, -0.65), 3.4, 1.3)
        o = eixos.c2p(0, 0)
        fasor = seta(o, eixos.c2p(I0, Q0), COR_RF, 6)
        ponto = Dot(eixos.c2p(I0, Q0), radius=0.09, color=WHITE)
        rot_pt = Text("(I, Q) estimado", font_size=18, color=WHITE).next_to(ponto, UP, buff=0.12)

        leg = self.legenda("Fluxo do ADC: o fasor gira 90° a cada amostra")
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in caixas], lag_ratio=0.1), run_time=1.5)
        leg = self.legenda("Para voltar ao vetor fixo, aplica-se uma rotação inversa ao par (y_{i+1}, y_i)", leg)
        self.play(Write(geral), run_time=2)
        self.play(FadeIn(passos))
        self.play(Create(eixos), FadeIn(rotulos), GrowArrow(fasor))

        janela = SurroundingRectangle(VGroup(caixas[0][0], caixas[1][0]), color=COR_DIGITAL, buff=0.08)
        atual = especifica(0)
        leg = self.legenda("A janela de 2 amostras desliza; a matriz muda de passo em passo", leg, COR_DIGITAL)
        self.play(Create(janela), Write(atual))
        self.play(GrowFromCenter(ponto), FadeIn(rot_pt))
        for i in range(1, 7):
            nova = especifica(i)
            alvo = SurroundingRectangle(VGroup(caixas[i][0], caixas[i + 1][0]), color=COR_DIGITAL, buff=0.08)
            self.play(Transform(janela, alvo), Transform(atual, nova), run_time=0.8)
            self.play(Indicate(ponto, color=WHITE, scale_factor=1.6), run_time=0.6)
        leg = self.legenda("Qualquer par consecutivo devolve o mesmo (I, Q)", leg, COR_RF)
        self.wait(0.8)

        notas = VGroup(
            Text("Matrizes só com 0, +1 e −1: selecionar dados e trocar o sinal", font_size=22, color=COR_DIGITAL),
            Text("Sem multiplicadores nem tabelas · equivale a um filtro FIR de 1ª ordem (2 coeficientes)",
                 font_size=20, color=GREY_A),
        ).arrange(DOWN, buff=0.15).move_to(P(-0.4, -2.75))
        leg = self.legenda("Custo mínimo no hardware e latência de apenas 2 amostras", leg, COR_I)
        self.play(FadeIn(notas, shift=UP * 0.2))
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 5
    def cena_generalizacao(self):
        self.titulo_cena("5 · Generalização: f_s = m·f_IF")
        formula = tex_partes([
            (r"\begin{pmatrix} I \\ Q \end{pmatrix} = ", WHITE),
            (r"\frac{1}{\sin\Delta\phi}", COR_ERRO),
            (r"\begin{pmatrix} \cos(\phi + n\Delta\phi) & -\cos(\phi + (n+1)\Delta\phi) \\"
             r" -\sin(\phi + n\Delta\phi) & \sin(\phi + (n+1)\Delta\phi) \end{pmatrix}"
             r"\begin{pmatrix} y_{n+1} \\ y_n \end{pmatrix}", WHITE),
        ], 28).move_to(P(0.4, 2.45))
        passo = tex(r"\Delta\phi = \frac{2\pi}{m}", GREY_A, 30).next_to(formula, LEFT, buff=0.4)
        if passo.get_left()[0] < -6.9:
            VGroup(passo, formula).shift(RIGHT * (-6.9 - passo.get_left()[0]))

        eixos, rotulos = plano(P(-3.1, -1.2), 3.9, 1.5)
        o = eixos.c2p(0, 0)
        z = np.array([0.55, 0.6])
        eps = 0.09
        dth = ValueTracker(90.0)

        def direcoes():
            d = np.deg2rad(dth.get_value())
            return np.array([0.0, 1.0]), np.array([np.sin(d), np.cos(d)])

        def faixa(d, cor):
            y = float(np.dot(z, d))
            tg = np.array([d[1], -d[0]])
            L = 1.45
            cantos = [(y - eps) * d - L * tg, (y - eps) * d + L * tg, (y + eps) * d + L * tg, (y + eps) * d - L * tg]
            poly = Polygon(*[eixos.c2p(*c) for c in cantos], stroke_width=0, fill_color=cor, fill_opacity=0.2)
            centro = Line(eixos.c2p(*(y * d - L * tg)), eixos.c2p(*(y * d + L * tg)), color=cor, stroke_width=3)
            return VGroup(poly, centro)

        def paralelogramo():
            d1, d2 = direcoes()
            A = np.array([d1, d2])
            y = A @ z
            vs = [np.linalg.solve(A, y + eps * np.array(s)) for s in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
            return Polygon(*[eixos.c2p(*v) for v in vs], color=COR_ERRO, stroke_width=3,
                           fill_color=COR_ERRO, fill_opacity=0.45)

        f1 = always_redraw(lambda: faixa(direcoes()[0], COR_Q))
        f2 = always_redraw(lambda: faixa(direcoes()[1], COR_I))
        incerteza = always_redraw(paralelogramo)
        fasor = seta(o, eixos.c2p(*z), COR_RF, 5)

        def leituras():
            d = dth.get_value()
            s = abs(np.sin(np.deg2rad(d)))
            return VGroup(
                Text(f"Δφ = {d:.0f}°   (m ≈ {360 / d:.1f})", font_size=24, color=WHITE),
                Text(f"amplificação do ruído ∝ 1/|sin Δφ| = {1 / s:.2f}", font_size=22,
                     color=COR_ERRO if s < 0.6 else GREY_A),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(P(3.5, 0.6))

        painel = always_redraw(leituras)
        explica = VGroup(
            Text("Cada amostra = projeção do fasor numa direção", font_size=19, color=GREY_A),
            Text("(uma faixa, com a largura do ruído)", font_size=19, color=GREY_A),
            Text("(I, Q) fica no cruzamento das duas faixas", font_size=19, color=COR_ERRO),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to(P(3.5, -1.3))

        leg = self.legenda("Com outro inteiro m, duas amostras consecutivas ainda formam um sistema 2×2")
        self.play(Write(formula), FadeIn(passo), run_time=2)
        self.play(Indicate(formula[1], color=COR_ERRO))
        self.play(Create(eixos), FadeIn(rotulos), GrowArrow(fasor))
        leg = self.legenda("Geometria: cada amostra (com ruído) restringe o fasor a uma faixa", leg)
        self.play(FadeIn(f1), FadeIn(f2), FadeIn(explica))
        self.play(FadeIn(incerteza), FadeIn(painel))
        leg = self.legenda("Δφ = 90°: faixas perpendiculares, região de incerteza mínima", leg, COR_I)
        self.wait(1)
        leg = self.legenda("Δφ longe de 90° (ou 270°): sin Δφ pequeno, a incerteza explode", leg, COR_ERRO)
        self.play(dth.animate.set_value(25), run_time=4)
        self.wait(0.8)
        self.play(dth.animate.set_value(155), run_time=4)
        self.wait(0.6)
        self.play(dth.animate.set_value(90), run_time=2.5)
        leg = self.legenda("Por isso o passo de 90° (f_s = 4·f_IF) é o caso ótimo", leg)
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 6
    def cena_offset(self):
        self.titulo_cena("6 · Limitações: offset DC e erro de fase")
        c = 0.18
        estimativas = [(I0 + c, Q0 + c), (I0 + c, Q0 - c), (I0 - c, Q0 - c), (I0 - c, Q0 + c)]
        amostras_txt = tex_partes([(r"Q+c,\ ", COR_Q), (r"I+c,\ ", COR_I), (r"-Q+c,\ ", COR_Q),
                                   (r"-I+c,\ ", COR_I), (r"\dots", WHITE)], 30).move_to(P(3.4, 2.55))
        rot_am = Text("amostras com offset c:", font_size=20, color=COR_ERRO2).next_to(amostras_txt, LEFT, buff=0.25)

        eixos, rotulos = plano(P(-4.0, -0.7), 4.0, 1.3)
        o = eixos.c2p(0, 0)
        fasor = seta(o, eixos.c2p(I0, Q0), COR_RF, 6)
        quadrado = DashedVMobject(Polygon(*[eixos.c2p(*e) for e in estimativas], color=COR_ERRO2,
                                          stroke_width=2), num_dashes=24)
        ponto = Dot(eixos.c2p(*estimativas[0]), radius=0.09, color=COR_ERRO2)

        ax_i = eixos_tempo(P(3.4, 0.75), 6.0, 1.55, [0, 12, 1], [0, 1.2, 0.5])
        ax_q = eixos_tempo(P(3.4, -1.55), 6.0, 1.55, [0, 12, 1], [0, 1.2, 0.5])
        rot_i = rotulo_eixo(ax_i, Text("I estimado [n]", font_size=20, color=COR_I))
        rot_q = rotulo_eixo(ax_q, Text("Q estimado [n]", font_size=20, color=COR_Q))
        ref_i = DashedLine(ax_i.c2p(0, I0), ax_i.c2p(12, I0), color=COR_RF, stroke_width=2)
        ref_q = DashedLine(ax_q.c2p(0, Q0), ax_q.c2p(12, Q0), color=COR_RF, stroke_width=2)

        leg = self.legenda("Um offset DC c na entrada do ADC soma c a todas as amostras", None, COR_ERRO2)
        self.play(FadeIn(rot_am), Write(amostras_txt))
        self.play(Create(eixos), FadeIn(rotulos), GrowArrow(fasor))
        self.play(Create(ax_i), Create(ax_q), FadeIn(rot_i), FadeIn(rot_q), Create(ref_i), Create(ref_q))
        self.play(GrowFromCenter(ponto))
        leg = self.legenda("Após a rotação, o erro muda de sinal a cada passo: o ponto salta num quadrado", leg, COR_ERRO2)
        hastes = VGroup()
        for n in range(12):
            ei, eq = estimativas[n % 4]
            hi = haste(ax_i, n, ei, COR_I, 0.06, 3)
            hq = haste(ax_q, n, eq, COR_Q, 0.06, 3)
            hastes.add(hi, hq)
            anims = [ponto.animate.move_to(eixos.c2p(ei, eq)), GrowFromPoint(hi, ax_i.c2p(n, 0)),
                     GrowFromPoint(hq, ax_q.c2p(n, 0))]
            if n == 3:
                anims.append(Create(quadrado))
            self.play(*anims, run_time=0.55 if n < 4 else 0.3)
        leg = self.legenda("Ondulação com período de 4 amostras: aparece exatamente em f_s/4 = f_IF", leg, COR_ERRO)
        self.play(Indicate(hastes, color=COR_ERRO, scale_factor=1.05))
        leg = self.legenda("Erros de fase (passo diferente de 90°) deixam a mesma assinatura: ripple em f_IF",
                           leg, COR_ERRO)
        self.wait(2)
        self.limpar()

    def cena_harmonicas(self):
        self.titulo_cena("6 · Limitações: aliasing de harmônicas")
        fs = 4.0
        ax = Axes(x_range=[0, 7.6, 1], y_range=[0, 1.25, 0.5], x_length=12.4, y_length=2.1,
                  axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO},
                  y_axis_config={"include_tip": False}).move_to(P(0, 1.1))
        marcas = marcar_x(ax, range(8), [str(k) for k in range(8)])
        rot_f = Text("f / f_IF", font_size=18, color=COR_EIXO).next_to(ax.x_axis.get_end(), UP, buff=0.12)
        zona = Polygon(ax.c2p(0, 0), ax.c2p(0, 1.2), ax.c2p(fs / 2, 1.2), ax.c2p(fs / 2, 0),
                       stroke_width=0, fill_color=COR_DIGITAL, fill_opacity=0.12)
        l_nyq = DashedLine(ax.c2p(fs / 2, 0), ax.c2p(fs / 2, 1.2), color=COR_DIGITAL, stroke_width=3)
        r_nyq = tex(r"f_s/2", COR_DIGITAL, 26).next_to(l_nyq, UP, buff=0.08)
        l_fs = DashedLine(ax.c2p(fs, 0), ax.c2p(fs, 1.2), color=GREY_B, stroke_width=2)
        r_fs = tex(r"f_s", GREY_B, 26).next_to(l_fs, UP, buff=0.08)
        raias = {k: raia(ax, k, ALTURAS[k], COR_I if k == 1 else GREY_B) for k in range(1, 8)}
        rots = {k: Text(f"{k}ª", font_size=16, color=COR_I if k == 1 else GREY_A
                        ).next_to(ax.c2p(k, ALTURAS[k]), UP, buff=0.06) for k in range(1, 8)}

        leg = self.legenda("Não linearidades de mixers e ADCs geram harmônicas de f_IF")
        self.play(Create(ax), FadeIn(marcas), FadeIn(rot_f))
        self.play(GrowArrow(raias[1]), FadeIn(rots[1]))
        self.play(LaggedStart(*[AnimationGroup(GrowArrow(raias[k]), FadeIn(rots[k])) for k in range(2, 8)],
                              lag_ratio=0.2), run_time=2)
        leg = self.legenda("Com f_s = 4·f_IF, Nyquist fica em 2·f_IF: o que está acima dobra para dentro", leg,
                           COR_DIGITAL)
        self.play(FadeIn(zona), Create(l_nyq), FadeIn(r_nyq), Create(l_fs), FadeIn(r_fs))

        pos, grupos = posicoes_alias(fs)
        novos = {}
        anims = []
        for k in range(2, 8):
            cai = abs(alias(k, fs) - 1) < 1e-6
            novos[k] = raia(ax, pos[k], ALTURAS[k], COR_ERRO if cai else GREY_B)
            anims.append(ReplacementTransform(raias[k], novos[k], path_arc=PI / 2))
        self.play(*anims, *[FadeOut(rots[k]) for k in range(2, 8)], run_time=3)
        rot_grupos = VGroup()
        for a, ks in grupos.items():
            outras = [k for k in ks if k != 1]
            if not outras:
                continue
            txt = ", ".join(f"{k}ª" for k in outras)
            if 1 in ks:
                rot_grupos.add(Text(txt + "  →  sobre f_IF!", font_size=20, color=COR_ERRO
                                    ).next_to(ax.c2p(1.25, 0.95), RIGHT, buff=0.05))
            else:
                rot_grupos.add(Text(txt, font_size=16, color=GREY_A).next_to(
                    ax.c2p(a, max(ALTURAS[k] for k in outras)), UP, buff=0.08))
        self.play(FadeIn(rot_grupos))
        leg = self.legenda("A 2ª cai sobre Nyquist; 3ª, 5ª e 7ª caem exatamente em cima da fundamental", leg,
                           COR_ERRO)
        self.play(*[Indicate(novos[k], color=COR_ERRO) for k in (3, 5, 7)])
        self.wait(0.8)

        # Domínio do tempo: a 3ª harmônica gera as mesmas amostras de um sinal em f_IF
        ax_t = eixos_tempo(P(0, -1.75), 12, 1.8, [0, 2, 0.25], [-1.0, 1.0, 0.5])
        rot_t = rotulo_eixo(ax_t, Text("3ª harmônica (vermelho) × senoide em f_IF (tracejada)", font_size=20,
                                       color=GREY_A))
        h3 = ax_t.plot(lambda x: 0.8 * np.sin(3 * TAU * x), x_range=[0, 2, 0.005], color=COR_ERRO, stroke_width=3)
        h1 = DashedVMobject(ax_t.plot(lambda x: -0.8 * np.sin(TAU * x), x_range=[0, 2, 0.005],
                                      color=COR_I, stroke_width=4), num_dashes=50)
        pts = VGroup(*[Dot(ax_t.c2p(k / 4, 0.8 * np.sin(3 * TAU * k / 4)), radius=0.08, color=WHITE)
                       for k in range(9)])
        leg = self.legenda("No tempo: amostrada 4 vezes por período, a 3ª harmônica…", leg)
        self.play(Create(ax_t), FadeIn(rot_t))
        self.play(Create(h3), run_time=1.5)
        self.play(LaggedStart(*[GrowFromCenter(p) for p in pts], lag_ratio=0.1))
        leg = self.legenda("…dá as MESMAS amostras de um sinal em f_IF: impossível separar por filtragem", leg,
                           COR_ERRO)
        self.play(Create(h1), run_time=2)
        self.play(Indicate(pts, color=COR_ERRO))
        self.wait(1.8)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo")
        pros = VGroup(
            Text("Vantagens", font_size=28, color=COR_I, weight=BOLD),
            Text("• um único ADC, sem desbalanço I/Q", font_size=20),
            Text("• (I, Q) a partir de só 2 amostras", font_size=20),
            Text("• só seleção e troca de sinal", font_size=20),
            Text("• latência mínima: ideal para malhas rápidas", font_size=20),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(P(-3.4, 0.6))
        contras = VGroup(
            Text("Limitações", font_size=28, color=COR_ERRO, weight=BOLD),
            Text("• exige f_s = 4·f_IF exato", font_size=20),
            Text("• offset e erro de fase: ripple em f_IF", font_size=20),
            Text("• harmônicas ímpares caem sobre a portadora", font_size=20),
            Text("• Δφ longe de 90°: sensível a ruído", font_size=20),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(P(3.4, 0.6))
        sep = Line(P(0, 2.4), P(0, -1.3), color=COR_EIXO, stroke_width=2)
        final = Text("Saídas: Non-IQ sampling (f_s/f_IF = N/M) e Digital Down Conversion",
                     font_size=24, color=COR_DIGITAL).move_to(P(0, -2.4))
        self.play(FadeIn(pros[0]), FadeIn(contras[0]), Create(sep))
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in pros[1:]], lag_ratio=0.3), run_time=2)
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in contras[1:]], lag_ratio=0.3), run_time=2)
        self.play(Write(final), run_time=1.5)
        self.wait(2.5)
        self.limpar()
