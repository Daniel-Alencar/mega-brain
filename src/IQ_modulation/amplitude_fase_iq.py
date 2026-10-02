# -*- coding: utf-8 -*-
"""
Como medir amplitude e fase de uma onda de RF com detecção I/Q
==============================================================

Renderização (a partir da raiz do repositório):
    manim -pql src/IQ_modulation/amplitude_fase_iq.py AmplitudeFaseIQ   # rascunho
    manim -pqh src/IQ_modulation/amplitude_fase_iq.py AmplitudeFaseIQ   # final

Requer LaTeX (MathTex e DecimalNumber).

Roteiro:
    1. O que são amplitude e fase: altura da onda e adiantamento em relação ao LO.
    2. O truque do LO: girar junto com ele "congela" o fasor do RF.
       Demodular = multiplicar por e^{-jωt}; parte real = mixer I, parte
       imaginária = mixer Q.
    3. Por que um mixer só não basta: ele mede UMA projeção, ½·A·cos φ, e
       infinitos pares (A, φ) dão a mesma saída. Um segundo mixer com o LO
       deslocado de 90° mede a outra projeção e resolve a ambiguidade.
    4. De (I, Q) para (A, φ): Pitágoras e atan2 (e por que não arctan(Q/I)).
    5. A(t) e φ(t) em tempo real: enchimento da cavidade e salto de fase.
    6. Os três esquemas da Fig. 5 (Schilcher): detector de amplitude e fase,
       I/Q analógico e I/Q digital (DDC).

Convenção (a mesma de "Modulação IQ.md"):
    s(t) = A·cos(ωt + φ) = I·cos(ωt) − Q·sin(ωt),  I = A·cos φ,  Q = A·sin φ
    LO_I = cos(ωt)  ->  LPF{s·LO_I} = ½·A·cos φ = I/2
    LO_Q = −sin(ωt) ->  LPF{s·LO_Q} = ½·A·sin φ = Q/2
"""

import numpy as np
from manim import *

COR_RF = BLUE            # sinal de RF / fasor (seu comprimento é A)
COR_LO = GREY_A          # oscilador local (referência de fase)
COR_I = GOLD             # canal I
COR_Q = GREEN            # canal Q
COR_FASE = PINK          # fase φ
COR_ALERTA = RED         # ambiguidades e armadilhas
COR_CHIP = PURPLE_B      # FPGA
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}
OMEGA_TELA = TAU * 0.5   # velocidade de rotação do fasor na tela [rad/s]


# =============================================================================
# Utilitários
# =============================================================================
def P(x, y):
    return np.array([x, y, 0.0])


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


def bloco(rotulo, largura=1.2, altura=0.7, cor=WHITE, tamanho=24):
    caixa = RoundedRectangle(corner_radius=0.08, width=largura, height=altura,
                             color=cor, stroke_width=3)
    return VGroup(caixa, Text(rotulo, font_size=tamanho, color=cor).move_to(caixa))


def mixer(cor=WHITE, raio=0.32):
    c = Circle(radius=raio, color=cor, stroke_width=3)
    d = raio * 0.7
    x = VGroup(Line(P(-d, d), P(d, -d)), Line(P(-d, -d), P(d, d))).set_stroke(cor, 3)
    return VGroup(c, x)


def fio(pontos, cor=WHITE, largura=3):
    """Polilinha terminada em seta (fiação dos diagramas de blocos)."""
    g = VGroup(*[Line(pontos[k], pontos[k + 1], color=cor, stroke_width=largura)
                 for k in range(len(pontos) - 2)])
    g.add(Arrow(pontos[-2], pontos[-1], buff=0, color=cor, stroke_width=largura,
                max_tip_length_to_length_ratio=0.35))
    return g


def plano(centro, tam=5.6, alcance=1.4):
    eixos = Axes(x_range=[-alcance, alcance, 0.5], y_range=[-alcance, alcance, 0.5],
                 x_length=tam, y_length=tam,
                 axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO})
    eixos.move_to(centro)
    rot_i = Text("I", font_size=28, color=COR_I).next_to(eixos.x_axis.get_end(), DOWN, buff=0.15)
    rot_q = Text("Q", font_size=28, color=COR_Q).next_to(eixos.y_axis.get_end(), LEFT, buff=0.15)
    return eixos, VGroup(rot_i, rot_q)


def leitura(rotulo, func, cor, casas=2, unidade=None, sinal=True, tamanho=32):
    """Rótulo MathTex + número que se atualiza sozinho a partir de func()."""
    lab = MathTex(rotulo, color=cor, font_size=tamanho)
    num = DecimalNumber(func(), num_decimal_places=casas, unit=unidade, include_sign=sinal,
                        color=cor, font_size=tamanho).next_to(lab, RIGHT, buff=0.15)
    num.add_updater(lambda m: m.set_value(func()).next_to(lab, RIGHT, buff=0.15))
    return VGroup(lab, num)


def suave(u):
    u = np.clip(u, 0.0, 1.0)
    return 3 * u**2 - 2 * u**3


# =============================================================================
# Cena
# =============================================================================
class AmplitudeFaseIQ(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_o_que_medir()
        self.cena_referencial()
        self.cena_um_mixer()
        self.cena_polar()
        self.cena_tempo_real()
        self.cena_fig5()
        self.encerramento()

    # ------------------------------------------------------------- utilidades
    def titulo_cena(self, texto):
        t = Text(texto, font_size=32, weight=BOLD).to_corner(UL, buff=0.35)
        linha = Line(t.get_corner(DL), t.get_corner(DR), color=COR_EIXO,
                     stroke_width=2).shift(DOWN * 0.12)
        self.play(Write(t), Create(linha), run_time=1)
        return VGroup(t, linha)

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
        rastreadores = [m for m in self.mobjects if isinstance(m, ValueTracker)]
        self.remove(*rastreadores)
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        self.wait(0.2)

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Como medir amplitude e fase de uma onda de RF", font_size=44, weight=BOLD)
        sub = MathTex(r"y(t) = A\cdot\sin(\omega t + \varphi_0)", r"\;\longrightarrow\;", r"A,\ \varphi_0",
                      font_size=44)
        sub[0].set_color(COR_RF)
        sub[2].set_color(COR_FASE)
        ref = Text("detecção I/Q · T. Schilcher, Fig. 5", font_size=24, color=COR_EIXO)
        g = VGroup(titulo, sub, ref).arrange(DOWN, buff=0.45)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2))
        self.play(FadeIn(ref))
        self.wait(1.2)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_o_que_medir(self):
        self.titulo_cena("1 · O que são amplitude e fase?")
        A = ValueTracker(1.0)
        fi = ValueTracker(np.deg2rad(60))

        ax = Axes(x_range=[0, 3, 0.5], y_range=[-1.45, 1.45, 0.5], x_length=12.4, y_length=4.4,
                  axis_config=EIXO_CFG).move_to(P(0, -0.1))
        rot_t = Text("tempo (em períodos do LO) →", font_size=18, color=COR_EIXO).next_to(
            ax, DOWN, buff=0.08).align_to(ax, RIGHT)
        lo = DashedVMobject(ax.plot(lambda x: np.cos(TAU * x), x_range=[0, 3, 0.005],
                                    color=COR_LO, stroke_width=3), num_dashes=120)
        rf = always_redraw(lambda: ax.plot(lambda x: A.get_value() * np.cos(TAU * x + fi.get_value()),
                                           x_range=[0, 3, 0.005], color=COR_RF, stroke_width=4))
        leg = VGroup(MathTex(r"\mathrm{LO} = \cos(\omega t)", color=COR_LO, font_size=34),
                     MathTex(r"s(t) = A\cos(\omega t + \varphi)", color=COR_RF, font_size=34)
                     ).arrange(RIGHT, buff=1.0).next_to(ax, UP, buff=0.1).align_to(ax, LEFT)

        def x_pico():  # pico do RF mais próximo do pico do LO em x = 2
            return 2 - fi.get_value() / TAU

        seta_a = always_redraw(lambda: DoubleArrow(ax.c2p(x_pico(), 0), ax.c2p(x_pico(), A.get_value()),
                                                   buff=0, color=COR_RF, stroke_width=4,
                                                   max_tip_length_to_length_ratio=0.25))
        rot_a = MathTex("A", color=COR_RF, font_size=36)
        rot_a.add_updater(lambda m: m.next_to(ax.c2p(x_pico(), A.get_value() / 2), LEFT, buff=0.12))

        def marcador_fase():
            x1, y_m = x_pico(), 1.32
            g = VGroup(DashedLine(ax.c2p(x1, A.get_value()), ax.c2p(x1, y_m), color=COR_FASE,
                                  stroke_width=2, dash_length=0.06),
                       DashedLine(ax.c2p(2, 1), ax.c2p(2, y_m), color=COR_LO, stroke_width=2, dash_length=0.06))
            if 2 - x1 > 0.015:
                g.add(DoubleArrow(ax.c2p(x1, y_m), ax.c2p(2, y_m), buff=0, color=COR_FASE,
                                  stroke_width=3, max_tip_length_to_length_ratio=0.3))
            return g
        fase = always_redraw(marcador_fase)
        rot_fase = MathTex(r"\varphi = \omega\,\Delta t", color=COR_FASE, font_size=32)
        rot_fase.add_updater(lambda m: m.next_to(ax.c2p((x_pico() + 2) / 2, 1.32), UP, buff=0.08))

        self.play(Create(ax), FadeIn(rot_t))
        self.play(Create(lo), FadeIn(leg[0]), run_time=1.5)
        leg_txt = self.legenda("Fase só existe em relação a uma referência: o oscilador local (LO)")
        self.play(Create(rf), FadeIn(leg[1]), run_time=1.5)

        leg_txt = self.legenda("Amplitude A: a altura da oscilação", leg_txt, COR_RF)
        self.play(GrowFromPoint(seta_a, ax.c2p(x_pico(), 0)), FadeIn(rot_a))
        self.play(A.animate.set_value(0.55), run_time=1.5)
        self.play(A.animate.set_value(1.0), run_time=1.5)

        leg_txt = self.legenda("Fase φ: quanto o RF está adiantado em relação ao LO (φ = ω·Δt)", leg_txt, COR_FASE)
        self.play(FadeIn(fase), FadeIn(rot_fase))
        self.play(fi.animate.set_value(np.deg2rad(120)), run_time=2)
        self.play(fi.animate.set_value(np.deg2rad(20)), run_time=2)
        self.play(fi.animate.set_value(np.deg2rad(60)), run_time=1.5)

        leg_txt = self.legenda("Em 500 MHz um período dura 2 ns: 1° de fase equivale a Δt ≈ 5,6 ps!", leg_txt)
        self.wait(1.5)
        leg_txt = self.legenda("Medir pico e atraso direto na RF é inviável: precisamos de um truque", leg_txt)
        nota = Text("Obs.: Schilcher escreve y(t) = A·sin(ωt + φ₀): é a mesma onda, "
                    "com a referência deslocada de 90°", font_size=18, color=COR_EIXO).next_to(
            leg_txt, UP, buff=0.15)
        self.play(FadeIn(nota))
        self.wait(2)
        self.limpar()

    # ================================================================== CENA 2
    def cena_referencial(self):
        self.titulo_cena("2 · O truque: girar junto com o LO")
        pl, rot = plano(P(-3.5, -0.35), 5.6)
        o = pl.c2p(0, 0)
        A0, F0 = 0.95, np.deg2rad(50)
        k = ValueTracker(0.0)       # 0 = referencial do laboratório; 1 = girando com o LO
        theta = ValueTracker(0.0)   # ângulo do LO na tela

        def pt(r, a):
            return pl.c2p(r * np.cos(a), r * np.sin(a))

        lo = always_redraw(lambda: seta(o, pt(1.2, theta.get_value()), COR_LO, 5))
        rf = always_redraw(lambda: seta(o, pt(A0, theta.get_value() + F0), COR_RF, 7))
        rot_lo = Text("LO", font_size=20, color=COR_LO).add_updater(
            lambda m: m.move_to(pt(1.2, theta.get_value())
                                + 0.3 * np.array([-np.sin(theta.get_value()), np.cos(theta.get_value()), 0])))
        rot_rf = MathTex("A", color=COR_RF, font_size=32).add_updater(
            lambda m: m.move_to(pt(A0 + 0.2, theta.get_value() + F0 + 0.12)))
        arco = always_redraw(lambda: Arc(radius=0.55, start_angle=theta.get_value(), angle=F0,
                                         arc_center=o, color=COR_FASE, stroke_width=3))
        rot_phi = MathTex(r"\varphi", color=COR_FASE, font_size=32).add_updater(
            lambda m: m.move_to(pt(0.42, theta.get_value() + F0 / 2)))

        explic = VGroup(
            Text("Laboratório: RF e LO giram", font_size=24, color=GREY_A),
            Text("juntos, a ω (500 MHz).", font_size=24, color=GREY_A),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to(P(3.3, 1.6))

        self.play(Create(pl), FadeIn(rot))
        self.play(FadeIn(lo), FadeIn(rf), FadeIn(rot_lo), FadeIn(rot_rf))
        leg = self.legenda("A onda de RF é um fasor de comprimento A girando com velocidade ω")
        theta.add_updater(lambda m, dt: m.increment_value(OMEGA_TELA * (1 - k.get_value()) * dt))
        self.add(theta)
        self.wait(3)
        self.play(Create(arco), FadeIn(rot_phi), FadeIn(explic))
        leg = self.legenda("O LO gira na mesma velocidade: o ângulo entre os dois é sempre φ", leg, COR_FASE)
        self.wait(4)

        leg = self.legenda("Truque: olhar o plano girando junto com o LO (como num carrossel)…", leg)
        self.play(k.animate.set_value(1.0), run_time=4, rate_func=smooth)
        alvo = np.ceil(theta.get_value() / TAU) * TAU
        self.play(theta.animate.set_value(alvo), run_time=1.5)
        leg = self.legenda("…e o fasor do RF fica PARADO: comprimento A, ângulo φ", leg, COR_RF)
        self.wait(1)

        # Projeções do fasor congelado = I e Q
        I0, Q0 = A0 * np.cos(F0), A0 * np.sin(F0)
        seg_i = Line(o, pl.c2p(I0, 0), color=COR_I, stroke_width=9)
        seg_q = Line(o, pl.c2p(0, Q0), color=COR_Q, stroke_width=9)
        pr_i = DashedLine(pl.c2p(I0, Q0), pl.c2p(I0, 0), color=COR_I, stroke_width=2, dash_length=0.08)
        pr_q = DashedLine(pl.c2p(I0, Q0), pl.c2p(0, Q0), color=COR_Q, stroke_width=2, dash_length=0.08)
        r_i = MathTex(r"I = A\cos\varphi", color=COR_I, font_size=30).next_to(seg_i, DOWN, buff=0.15)
        r_q = MathTex(r"Q = A\sin\varphi", color=COR_Q, font_size=30).next_to(seg_q, LEFT, buff=0.1)
        self.play(Create(pr_i), Create(pr_q))
        self.play(Create(seg_i), Create(seg_q), Write(r_i), Write(r_q))
        leg = self.legenda("I e Q são simplesmente as coordenadas do fasor parado", leg)

        # Matemática do "carrossel"
        f1 = MathTex(r"s(t) = A\cos(\omega t+\varphi)", color=COR_RF, font_size=32)
        t2 = VGroup(Text("girar junto com o LO = multiplicar por", font_size=20, color=GREY_A),
                    MathTex(r"e^{-j\omega t}", font_size=32)).arrange(RIGHT, buff=0.15)
        f3 = MathTex(r"s(t)\,e^{-j\omega t}", r"=", r"\tfrac{A}{2}e^{j\varphi}", r"+",
                     r"\tfrac{A}{2}e^{-j(2\omega t+\varphi)}", font_size=34)
        f3[2].set_color(COR_RF)
        f3[4].set_color(GREY_B)
        b1 = Brace(f3[2], DOWN, color=COR_RF, buff=0.08)
        b1t = Text("parado", font_size=16, color=COR_RF).next_to(b1, DOWN, buff=0.06)
        b2 = Brace(f3[4], DOWN, color=GREY_B, buff=0.08)
        b2t = Text("gira a 2ω\n→ o LPF remove", font_size=16, color=GREY_B,
                   line_spacing=0.9).next_to(b2, DOWN, buff=0.06)
        bloco_f3 = VGroup(f3, b1, b1t, b2, b2t)
        f4 = MathTex(r"e^{-j\omega t} = ", r"\cos(\omega t)", r"\;+\;j\,", r"\bigl(-\sin(\omega t)\bigr)",
                     font_size=32)
        f4[1].set_color(COR_I)
        f4[3].set_color(COR_Q)
        t5 = VGroup(Text("parte real → mixer I", font_size=20, color=COR_I),
                    Text("parte imaginária → mixer Q", font_size=20, color=COR_Q)).arrange(RIGHT, buff=0.5)
        f6 = MathTex(r"\xrightarrow{\;\mathrm{LPF}\;}\ \tfrac{1}{2}\,(I + jQ) = \tfrac{A}{2}\,e^{j\varphi}",
                     font_size=36)
        col = VGroup(f1, t2, bloco_f3, f4, t5, f6).arrange(DOWN, buff=0.32).move_to(P(3.45, -0.3))

        self.play(FadeOut(explic), Write(f1))
        self.play(FadeIn(t2))
        leg = self.legenda("Matematicamente, 'girar junto' é multiplicar pelo LO complexo", leg)
        self.play(Write(f3), run_time=1.5)
        self.play(GrowFromCenter(b1), FadeIn(b1t), GrowFromCenter(b2), FadeIn(b2t))
        self.play(Write(f4))
        leg = self.legenda("Os dois mixers da demodulação I/Q são as partes real e imaginária", leg)
        self.play(FadeIn(t5, shift=UP * 0.1))
        self.play(Write(f6))
        self.play(Indicate(f6, color=WHITE))
        self.wait(2)
        self.limpar()

    # ================================================================== CENA 3
    def cena_um_mixer(self):
        self.titulo_cena("3 · Por que um mixer só não basta")
        A = ValueTracker(1.0)
        fi = ValueTracker(np.deg2rad(60))
        k = ValueTracker(0.0)   # deslocamento do LO em unidades de 90°

        ax1 = Axes(x_range=[0, 2, 0.5], y_range=[-1.3, 1.3, 0.5], x_length=7.0, y_length=2.1,
                   axis_config=EIXO_CFG).move_to(P(-3.25, 1.3))
        ax2 = Axes(x_range=[0, 2, 0.5], y_range=[-1.3, 1.3, 0.5], x_length=7.0, y_length=2.1,
                   axis_config=EIXO_CFG).move_to(P(-3.25, -1.6))

        def lo_f(x):
            return np.cos(TAU * x + k.get_value() * PI / 2)

        def rf_f(x):
            return A.get_value() * np.cos(TAU * x + fi.get_value())

        def media():
            return 0.5 * A.get_value() * np.cos(fi.get_value() - k.get_value() * PI / 2)

        def cor_canal():
            return interpolate_color(COR_I, COR_Q, k.get_value())

        c_lo = always_redraw(lambda: DashedVMobject(ax1.plot(lo_f, x_range=[0, 2, 0.01], color=COR_LO,
                                                             stroke_width=3), num_dashes=60))
        c_rf = always_redraw(lambda: ax1.plot(rf_f, x_range=[0, 2, 0.01], color=COR_RF, stroke_width=4))
        c_prod = always_redraw(lambda: ax2.plot(lambda x: rf_f(x) * lo_f(x), x_range=[0, 2, 0.01],
                                                color=cor_canal(), stroke_width=3))
        l_media = always_redraw(lambda: DashedLine(ax2.c2p(0, media()), ax2.c2p(2, media()), color=WHITE,
                                                   stroke_width=4, dash_length=0.12))
        r_media = Text("média", font_size=16, color=WHITE).add_updater(
            lambda m: m.next_to(ax2.c2p(2, media()), RIGHT, buff=0.08))

        leg_rf = MathTex(r"s(t) = A\cos(\omega t+\varphi)", color=COR_RF, font_size=28)
        leg_lo = MathTex(r"\mathrm{LO} = \cos(\omega t)", color=COR_LO, font_size=28)
        cab1 = VGroup(leg_rf, leg_lo).arrange(RIGHT, buff=0.6).next_to(ax1, UP, buff=0.05).align_to(ax1, LEFT)
        cab2 = Text("produto do mixer: s(t)·LO", font_size=20, color=GREY_A).next_to(
            ax2, UP, buff=0.05).align_to(ax2, LEFT)
        f_lpf = MathTex(r"\xrightarrow{\;\mathrm{LPF}\;}\ \tfrac{1}{2}A\cos\varphi", color=COR_I, font_size=30)
        f_lpf.next_to(cab2, RIGHT, buff=0.35)
        saida = leitura(r"=", media, WHITE, casas=2, tamanho=30).next_to(f_lpf, RIGHT, buff=0.15)

        # Plano: a saída do LPF é a projeção do fasor sobre o "eixo de medição"
        pl, rot = plano(P(3.95, 0.15), 4.4)
        o2 = pl.c2p(0, 0)

        def e():
            a = k.get_value() * PI / 2
            return np.array([np.cos(a), np.sin(a)])

        def ep():
            a = k.get_value() * PI / 2
            return np.array([-np.sin(a), np.cos(a)])

        def z():
            return A.get_value() * np.array([np.cos(fi.get_value()), np.sin(fi.get_value())])

        def pr():
            return float(np.dot(z(), e()))

        fasor = always_redraw(lambda: seta(o2, pl.c2p(*z()), COR_RF, 6))
        seg = always_redraw(lambda: segmento(o2, pl.c2p(*(pr() * e())), cor_canal(), 8))
        proj = always_redraw(lambda: tracejada(pl.c2p(*z()), pl.c2p(*(pr() * e())), cor_canal(), 2))
        reta = always_redraw(lambda: DashedLine(pl.c2p(*(pr() * e() - 1.3 * ep())),
                                                pl.c2p(*(pr() * e() + 1.3 * ep())),
                                                color=interpolate_color(COR_ALERTA, COR_Q, k.get_value()),
                                                stroke_width=3, dash_length=0.1))
        nota_x2 = Text("(saída do LPF × 2 = projeção)", font_size=16, color=COR_EIXO).next_to(
            pl, DOWN, buff=0.05)

        # 1) Mixer + LPF
        self.play(Create(ax1), Create(ax2))
        self.play(Create(c_lo), FadeIn(leg_lo), Create(c_rf), FadeIn(leg_rf), run_time=1.5)
        leg = self.legenda("Mixer: multiplicar o RF pelo LO…")
        self.play(Create(c_prod), FadeIn(cab2), run_time=1.5)
        leg = self.legenda("…o produto oscila a 2ω em torno de um valor médio", leg)
        self.play(Create(l_media), FadeIn(r_media))
        leg = self.legenda("O filtro passa-baixas (LPF) fica só com a média: ½·A·cos φ", leg)
        self.play(Write(f_lpf), FadeIn(saida))

        self.play(Create(pl), FadeIn(rot), FadeIn(fasor), FadeIn(nota_x2))
        self.play(Create(proj), Create(seg))
        leg = self.legenda("A média muda com a fase: é a projeção do fasor no eixo I", leg)
        for graus in (0, 180, 60):
            self.play(fi.animate.set_value(np.deg2rad(graus)), run_time=2)

        # 2) A ambiguidade
        leg = self.legenda("Mas um número só não basta: todo fasor sobre a reta vermelha dá a MESMA saída",
                           leg, COR_ALERTA)
        self.play(Create(reta))

        def varrer(_, alfa, ida=True):
            graus = 60 - 120 * alfa if ida else -60 + 120 * alfa
            fi.set_value(np.deg2rad(graus))
            A.set_value(0.5 / np.cos(np.deg2rad(graus)))

        amb = Text("A = 1, φ = +60°   |   A = 0,5, φ = 0°   |   A = 1, φ = −60°\n"
                   "→ todos dão a mesma saída 0,25", font_size=17, color=COR_ALERTA,
                   line_spacing=1.1).move_to(P(3.95, -2.8))
        self.play(FadeIn(amb))
        self.play(UpdateFromAlphaFunc(ValueTracker(0), lambda m, a: varrer(m, a, True)), run_time=4)
        self.play(UpdateFromAlphaFunc(ValueTracker(0), lambda m, a: varrer(m, a, False)), run_time=4)
        leg = self.legenda("Amplitude e fase se confundem: um mixer mede só UMA projeção", leg, COR_ALERTA)
        self.wait(1)

        # 3) Segundo mixer: LO deslocado de 90°
        reta_i = DashedLine(pl.c2p(0.5, -1.3), pl.c2p(0.5, 1.3), color=COR_I, stroke_width=3, dash_length=0.1)
        seg_i = Line(o2, pl.c2p(0.5, 0), color=COR_I, stroke_width=8)
        self.add(reta_i, seg_i)
        leg = self.legenda("Solução: um segundo mixer com o LO deslocado de 90°", leg)
        novo_lo = MathTex(r"\mathrm{LO} = -\sin(\omega t)", color=COR_LO, font_size=28).move_to(leg_lo)
        novo_lpf = MathTex(r"\xrightarrow{\;\mathrm{LPF}\;}\ \tfrac{1}{2}A\sin\varphi", color=COR_Q,
                           font_size=30).move_to(f_lpf)
        self.play(FadeOut(amb), Transform(leg_lo, novo_lo), Transform(f_lpf, novo_lpf),
                  k.animate.set_value(1.0), run_time=3)
        leg = self.legenda("Girar a fase do LO em 90° = girar o eixo de medição: agora medimos ½·A·sin φ", leg)
        self.wait(1)

        cruz = always_redraw(lambda: Dot(pl.c2p(*z()), radius=0.1, color=WHITE))
        self.add(cruz)
        self.play(Flash(pl.c2p(*z()), color=WHITE, line_length=0.25))
        leg = self.legenda("Duas projeções ortogonais ⇒ duas retas ⇒ UM único ponto: o fasor", leg, COR_RF)
        self.wait(1)
        leg = self.legenda("Os mesmos três sinais agora dão pares (I, Q) diferentes: ambiguidade resolvida", leg)
        self.play(UpdateFromAlphaFunc(ValueTracker(0), lambda m, a: varrer(m, a, True)), run_time=4)
        self.play(UpdateFromAlphaFunc(ValueTracker(0), lambda m, a: varrer(m, a, False)), run_time=4)
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 4
    def cena_polar(self):
        self.titulo_cena("4 · De (I, Q) para amplitude e fase")
        pl, rot = plano(P(-3.5, -0.35), 5.6)
        o = pl.c2p(0, 0)
        A = ValueTracker(0.9)
        fi = ValueTracker(np.deg2rad(50))

        def I():
            return A.get_value() * np.cos(fi.get_value())

        def Q():
            return A.get_value() * np.sin(fi.get_value())

        seg_i = always_redraw(lambda: segmento(o, pl.c2p(I(), 0), COR_I, 9))
        seg_q = always_redraw(lambda: segmento(pl.c2p(I(), 0), pl.c2p(I(), Q()), COR_Q, 9))
        fasor = always_redraw(lambda: seta(o, pl.c2p(I(), Q()), COR_RF, 7))
        arco = always_redraw(lambda: Arc(radius=0.5, start_angle=0,
                                         angle=fi.get_value() if abs(fi.get_value()) > 0.02 else 0.02,
                                         arc_center=o, color=COR_FASE, stroke_width=3))
        r_i = MathTex("I", color=COR_I, font_size=32).add_updater(
            lambda m: m.next_to(pl.c2p(I() / 2, 0), DOWN if Q() >= 0 else UP, buff=0.12))
        r_q = MathTex("Q", color=COR_Q, font_size=32).add_updater(
            lambda m: m.next_to(pl.c2p(I(), Q() / 2), RIGHT if I() >= 0 else LEFT, buff=0.12))

        def pos_a(m):
            meio = np.array([I() / 2, Q() / 2])
            n = np.array([-np.sin(fi.get_value()), np.cos(fi.get_value())])
            if np.dot(n, np.array([I(), 0]) - meio) > 0:   # aponta para fora do triângulo
                n = -n
            m.move_to(pl.c2p(*(meio + 0.18 * n)))
        r_a = MathTex("A", color=COR_RF, font_size=32).add_updater(pos_a)
        r_f = MathTex(r"\varphi", color=COR_FASE, font_size=30).add_updater(
            lambda m: m.move_to(pl.c2p(0.38 * np.cos(fi.get_value() / 2), 0.38 * np.sin(fi.get_value() / 2))))

        f_a = MathTex(r"A = \sqrt{I^2 + Q^2}", color=COR_RF, font_size=42)
        f_a_t = Text("Pitágoras", font_size=18, color=COR_EIXO)
        f_f = MathTex(r"\varphi = \operatorname{atan2}(Q,\ I)", color=COR_FASE, font_size=42)
        f_f_t = Text("ângulo com o quadrante correto", font_size=18, color=COR_EIXO)
        formulas = VGroup(VGroup(f_a, f_a_t).arrange(DOWN, buff=0.08),
                          VGroup(f_f, f_f_t).arrange(DOWN, buff=0.08)).arrange(DOWN, buff=0.35)
        formulas.move_to(P(3.4, 1.55))
        leituras = VGroup(
            leitura("I =", I, COR_I), leitura("Q =", Q, COR_Q),
            leitura("A =", lambda: np.hypot(I(), Q()), COR_RF, sinal=False),
            leitura(r"\varphi =", lambda: np.degrees(np.arctan2(Q(), I())), COR_FASE, casas=1,
                    unidade=r"^\circ"),
        )
        grade = VGroup(VGroup(leituras[0], leituras[1]).arrange(RIGHT, buff=0.8),
                       VGroup(leituras[2], leituras[3]).arrange(RIGHT, buff=0.8)
                       ).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to(P(3.4, -0.35))
        nota = Text("(I e Q já multiplicados por 2 para compensar o ½ do mixer)", font_size=16,
                    color=COR_EIXO).next_to(grade, DOWN, buff=0.15)

        self.play(Create(pl), FadeIn(rot))
        self.play(FadeIn(fasor), Create(seg_i), Create(seg_q), FadeIn(r_i), FadeIn(r_q), FadeIn(r_a),
                  Create(arco), FadeIn(r_f))
        leg = self.legenda("I e Q são os catetos; A é a hipotenusa; φ é o ângulo")
        self.play(Write(f_a), FadeIn(f_a_t))
        self.play(Write(f_f), FadeIn(f_f_t))
        self.play(FadeIn(grade), FadeIn(nota))
        leg = self.legenda("Qualquer par (I, Q) medido vira (A, φ), amostra por amostra", leg)
        for a_alvo, f_alvo in [(0.9, 140), (0.6, 140), (0.6, -120), (1.0, -60), (0.9, 50)]:
            self.play(A.animate.set_value(a_alvo), fi.animate.set_value(np.deg2rad(f_alvo)), run_time=1.6)

        # Armadilha do arctan(Q/I)
        leg = self.legenda("Cuidado: arctan(Q/I) perde os sinais de I e Q", leg, COR_ALERTA)
        self.play(A.animate.set_value(0.85), fi.animate.set_value(np.deg2rad(45)), run_time=1.2)
        fantasma = seta(o, pl.c2p(0.85 * np.cos(PI / 4), 0.85 * np.sin(PI / 4)), COR_RF, 5).set_opacity(0.35)
        self.add(fantasma)
        self.play(fi.animate.set_value(np.deg2rad(-135)), run_time=2)
        armadilha = VGroup(
            MathTex(r"\arctan\!\left(\tfrac{0.6}{0.6}\right) = \arctan\!\left(\tfrac{-0.6}{-0.6}\right) = 45^\circ",
                    color=COR_ALERTA, font_size=30),
            MathTex(r"\operatorname{atan2}(0.6,\,0.6) = 45^\circ \qquad "
                    r"\operatorname{atan2}(-0.6,\,-0.6) = -135^\circ", color=COR_FASE, font_size=28),
        ).arrange(DOWN, buff=0.25).move_to(P(3.4, -2.35))
        self.play(FadeOut(nota), Write(armadilha[0]))
        leg = self.legenda("Quadrantes opostos dão o mesmo arctan; o atan2 usa os sinais e acerta", leg, COR_FASE)
        self.play(Write(armadilha[1]))
        self.wait(1.5)
        leg = self.legenda("Na FPGA, √ e atan2 costumam usar o algoritmo CORDIC (somas e shifts)", leg)
        self.wait(2)
        self.limpar()

    # ================================================================== CENA 5
    def cena_tempo_real(self):
        self.titulo_cena("5 · Acompanhando A(t) e φ(t) em tempo real")
        pl, rot = plano(P(-3.7, -0.45), 5.0)
        o = pl.c2p(0, 0)
        tau = ValueTracker(0.0)
        T = 10.0

        def amp(x):     # enchimento da cavidade
            return 1 - np.exp(-x / 1.8)

        def fase(x):    # 30° e depois um salto suave para −45°
            return 30 + (-45 - 30) * suave((x - 5.0) / 1.5)

        def iq(x):
            a, f = amp(x), np.deg2rad(fase(x))
            return a * np.cos(f), a * np.sin(f)

        def fase_medida(x):   # o que a FPGA calcula: atan2(Q, I)
            i, q = iq(x)
            return np.degrees(np.arctan2(q, i))

        cfg = dict(x_length=6.2, y_length=1.5, axis_config=EIXO_CFG)
        ax_iq = Axes(x_range=[0, T, 2], y_range=[-1.1, 1.1, 0.5], **cfg).move_to(P(3.45, 1.85))
        ax_a = Axes(x_range=[0, T, 2], y_range=[0, 1.2, 0.5], **cfg).move_to(P(3.45, -0.2))
        ax_f = Axes(x_range=[0, T, 2], y_range=[-90, 90, 45], **cfg).move_to(P(3.45, -2.25))
        ax_f.y_axis.add_numbers([-45, 0, 45], font_size=18)
        ax_f.y_axis.numbers.set_color(COR_EIXO)
        cab_iq = VGroup(MathTex("I(t)", color=COR_I, font_size=26), MathTex("Q(t)", color=COR_Q, font_size=26)
                        ).arrange(RIGHT, buff=0.3).next_to(ax_iq, UP, buff=0.03).align_to(ax_iq, LEFT)
        cab_a = MathTex(r"A(t) = \sqrt{I^2+Q^2}", color=COR_RF, font_size=26).next_to(
            ax_a, UP, buff=0.03).align_to(ax_a, LEFT)
        cab_f = MathTex(r"\varphi(t) = \operatorname{atan2}(Q, I)\ [^\circ]", color=COR_FASE, font_size=26
                        ).next_to(ax_f, UP, buff=0.03).align_to(ax_f, LEFT)

        def ate_agora(ax, func, cor, inicio=0.0):
            fim = max(tau.get_value(), inicio + 0.05)
            return ax.plot(func, x_range=[inicio, fim, 0.02], color=cor, stroke_width=3)

        c_i = always_redraw(lambda: ate_agora(ax_iq, lambda x: iq(x)[0], COR_I))
        c_q = always_redraw(lambda: ate_agora(ax_iq, lambda x: iq(x)[1], COR_Q))
        c_a = always_redraw(lambda: ate_agora(ax_a, amp, COR_RF))
        c_f = always_redraw(lambda: ate_agora(ax_f, fase_medida, COR_FASE, inicio=0.25))

        def ponta():
            return pl.c2p(*iq(tau.get_value()))
        fasor = always_redraw(lambda: seta(o, ponta(), COR_RF, 6))
        seg_i = always_redraw(lambda: segmento(o, pl.c2p(iq(tau.get_value())[0], 0), COR_I, 7))
        seg_q = always_redraw(lambda: segmento(o, pl.c2p(0, iq(tau.get_value())[1]), COR_Q, 7))
        dot = Dot(radius=0.06, color=WHITE).add_updater(lambda m: m.move_to(ponta()))

        self.play(Create(pl), FadeIn(rot))
        self.play(Create(ax_iq), Create(ax_a), Create(ax_f), FadeIn(cab_iq), FadeIn(cab_a), FadeIn(cab_f))
        self.add(fasor, seg_i, seg_q, dot, c_i, c_q, c_a, c_f)
        rastro = TracedPath(dot.get_center, stroke_color=BLUE_B, stroke_width=3)
        self.add(rastro)
        leg = self.legenda("Com a portadora congelada pelo LO, sobra só a variação LENTA de A e φ")
        self.play(tau.animate.set_value(5.0), run_time=5, rate_func=linear)
        t_ench = Text("enchimento", font_size=18, color=COR_RF).move_to(ax_a.c2p(1.6, 0.95))
        self.play(FadeIn(t_ench))
        leg = self.legenda("Exemplo: a cavidade enche (A sobe) e depois ocorre um salto de fase", leg)
        self.play(tau.animate.set_value(T), run_time=5, rate_func=linear)
        t_salto = Text("salto de fase", font_size=18, color=COR_FASE).move_to(ax_f.c2p(7.9, 45))
        self.play(FadeIn(t_salto))
        leg = self.legenda("A cada amostra: (I, Q) → (A, φ). É isso que o LLRF mede e regula", leg)
        self.wait(1.5)
        leg = self.legenda("Obs.: com A ≈ 0 (início) a fase não é definida: atan2(0, 0) é só ruído", leg)
        self.wait(2)
        self.limpar()

    # ================================================================== CENA 6
    def cena_fig5(self):
        self.titulo_cena("6 · Os três esquemas da Fig. 5 (Schilcher)")
        linhas = [self.esquema_a(2.0), self.esquema_b(0.0), self.esquema_c(-2.0)]
        for rotulo, diagrama, resumo in linhas:
            self.play(FadeIn(rotulo), run_time=0.6)
            self.play(Create(diagrama), run_time=1.6)
            self.play(Write(resumo), run_time=1.6)
            self.wait(0.6)
        destaques = [COR_ALERTA, COR_Q, COR_RF]
        textos = ["a) mede A e uma projeção da fase: ambíguo",
                  "b) mede as duas projeções: A e φ completos (mas com erros de hardware)",
                  "c) mede as duas projeções no digital: A e φ completos e precisos"]
        leg = None
        for (rotulo, diagrama, resumo), cor, txt in zip(linhas, destaques, textos):
            caixa = SurroundingRectangle(VGroup(rotulo, diagrama, resumo), color=cor, buff=0.1)
            leg = self.legenda(txt, leg, cor)
            self.play(Create(caixa))
            self.wait(1.2)
            self.play(FadeOut(caixa))
        self.wait(1)
        self.limpar()

    def esquema_a(self, y):
        rotulo = Text("a) Detector de\namplitude e fase", font_size=20, line_spacing=1.0).move_to(P(-5.6, y))
        yu, yd = y + 0.4, y - 0.4
        rf = Text("RF", font_size=20, color=COR_RF).move_to(P(-3.9, y))
        no = Dot(P(-3.3, y), radius=0.05)
        diodo = bloco("diodo", 0.9, 0.36, WHITE, 16).move_to(P(-1.8, yu))
        mx = mixer(WHITE, 0.17).move_to(P(-1.8, yd))
        lo = Text("LO", font_size=14, color=COR_LO).move_to(P(-1.8, yd - 0.45))
        adc_u = bloco("ADC", 0.7, 0.32, WHITE, 14).move_to(P(-0.3, yu))
        adc_d = bloco("ADC", 0.7, 0.32, WHITE, 14).move_to(P(-0.3, yd))
        out_u = MathTex("A", color=COR_RF, font_size=26).move_to(P(0.55, yu))
        out_d = MathTex(r"\propto A\cos\varphi", color=COR_FASE, font_size=24).move_to(P(0.95, yd))
        diagrama = VGroup(
            rf, no, diodo, mx, lo, adc_u, adc_d, out_u, out_d,
            Line(rf.get_right(), no.get_center(), color=COR_RF, stroke_width=3),
            fio([no.get_center(), P(-3.3, yu), diodo.get_left()]),
            fio([no.get_center(), P(-3.3, yd), mx.get_left()]),
            fio([lo.get_top(), mx.get_bottom()], COR_LO, 2),
            fio([diodo.get_right(), adc_u.get_left()]),
            fio([mx.get_right(), adc_d.get_left()]),
        )
        resumo = Text("Diodo → A (envelope).\nMixer = um canal I sozinho: ∝ A·cos φ\n"
                      "→ ambíguo (+φ e −φ iguais) e depende de A.", font_size=17, color=GREY_A,
                      line_spacing=1.0).move_to(P(2.0, y), aligned_edge=LEFT)
        return rotulo, diagrama, resumo

    def esquema_b(self, y):
        rotulo = Text("b) Detecção I/Q\nanalógica", font_size=20, line_spacing=1.0).move_to(P(-5.6, y))
        yu, yd = y + 0.4, y - 0.4
        rf = Text("RF", font_size=20, color=COR_RF).move_to(P(-3.9, y))
        no = Dot(P(-3.3, y), radius=0.05)
        mx_i = mixer(COR_I, 0.17).move_to(P(-1.8, yu))
        mx_q = mixer(COR_Q, 0.17).move_to(P(-1.8, yd))
        lo_i = Text("LO 0°", font_size=13, color=COR_LO).next_to(mx_i, UP, buff=0.05)
        lo_q = Text("LO 90°", font_size=13, color=COR_LO).next_to(mx_q, DOWN, buff=0.05)
        adc_u = bloco("ADC", 0.7, 0.32, WHITE, 14).move_to(P(-0.3, yu))
        adc_d = bloco("ADC", 0.7, 0.32, WHITE, 14).move_to(P(-0.3, yd))
        out_i = MathTex("I", color=COR_I, font_size=26).move_to(P(0.45, yu))
        out_q = MathTex("Q", color=COR_Q, font_size=26).move_to(P(0.45, yd))
        calc = MathTex(r"\to A,\ \varphi", font_size=26).move_to(P(1.25, y))
        diagrama = VGroup(
            rf, no, mx_i, mx_q, lo_i, lo_q, adc_u, adc_d, out_i, out_q, calc,
            Line(rf.get_right(), no.get_center(), color=COR_RF, stroke_width=3),
            fio([no.get_center(), P(-3.3, yu), mx_i.get_left()], COR_I),
            fio([no.get_center(), P(-3.3, yd), mx_q.get_left()], COR_Q),
            fio([mx_i.get_right(), adc_u.get_left()], COR_I),
            fio([mx_q.get_right(), adc_d.get_left()], COR_Q),
        )
        resumo = Text("Dois mixers 0°/90° → I e Q.\nA e φ calculados: √(I²+Q²) e atan2.\n"
                      "Sofre com erro de 90° e de ganho.", font_size=17, color=GREY_A,
                      line_spacing=1.0).move_to(P(2.0, y), aligned_edge=LEFT)
        return rotulo, diagrama, resumo

    def esquema_c(self, y):
        rotulo = Text("c) Amostragem I/Q\ndigital (DDC)", font_size=20, line_spacing=1.0).move_to(P(-5.6, y))
        rf = Text("RF", font_size=20, color=COR_RF).move_to(P(-3.9, y))
        mx = mixer(WHITE, 0.17).move_to(P(-2.7, y))
        lo = Text("LO", font_size=14, color=COR_LO).move_to(P(-2.7, y + 0.6))
        adc = bloco("ADC", 0.7, 0.36, WHITE, 14).move_to(P(-1.4, y))
        fpga = bloco("FPGA", 0.95, 0.42, COR_CHIP, 16).move_to(P(-0.15, y))
        out = MathTex(r"I,Q \to A,\varphi", font_size=24).move_to(P(1.15, y))
        diagrama = VGroup(
            rf, mx, lo, adc, fpga, out,
            fio([rf.get_right(), mx.get_left()], COR_RF),
            fio([lo.get_bottom(), mx.get_top()], COR_LO, 2),
            fio([mx.get_right(), adc.get_left()]),
            fio([adc.get_right(), fpga.get_left()]),
        )
        resumo = Text("1 mixer → IF, 1 ADC.\nI/Q com 90° numérico; A e φ na FPGA.\n"
                      "Padrão em LLRF modernos.", font_size=17, color=GREY_A,
                      line_spacing=1.0).move_to(P(2.0, y), aligned_edge=LEFT)
        return rotulo, diagrama, resumo

    # ============================================================ ENCERRAMENTO
    def encerramento(self):
        self.titulo_cena("Resumo")
        itens = VGroup(
            Text("Amplitude e fase são as coordenadas POLARES do fasor de RF.", font_size=26),
            Text("O LO congela o fasor: I e Q são suas coordenadas CARTESIANAS.", font_size=26),
            Text("Um mixer mede uma projeção (ambígua); dois mixers a 90° fixam o fasor.", font_size=26),
            MathTex(r"A = \sqrt{I^2+Q^2}", r"\qquad", r"\varphi = \operatorname{atan2}(Q,\ I)", font_size=44),
        ).arrange(DOWN, buff=0.5)
        itens[3][0].set_color(COR_RF)
        itens[3][2].set_color(COR_FASE)
        for item in itens:
            self.play(FadeIn(item, shift=UP * 0.2), run_time=1)
            self.wait(0.8)
        self.wait(2.5)
        self.limpar()
