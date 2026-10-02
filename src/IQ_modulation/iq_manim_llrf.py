# -*- coding: utf-8 -*-
"""
Detecção I/Q em LLRF: desmodulação analógica direta × amostragem digital (DDC)
==============================================================================

Renderização (Manim Community Edition):
    manim -pql iq_manim_llrf.py IQDemodulationComparison   # rascunho, 480p15
    manim -pqh iq_manim_llrf.py IQDemodulationComparison   # final, 1080p60

Dependências:
    pip install manim
    LaTeX é OPCIONAL: se `latex` e `dvisvgm` estiverem no PATH as fórmulas usam
    MathTex; caso contrário caem automaticamente para texto Unicode (Pango).
    (Debian/Ubuntu: sudo apt install texlive texlive-latex-extra dvisvgm)

Roteiro:
    Abertura
    Cena 1  - Fasor girante e decomposição I = A·cos φ, Q = A·sin φ
    Cena 2a - Esquema do demodulador analógico (Fig. 5b) e suas imperfeições
    Cena 2b - Geometria: eixos a 95° + ganho (1+ε) => círculo vira elipse
    Cena 3a - Esquema IF + ADC + FPGA (Fig. 5c) e amostragem síncrona
    Cena 3b - Dentro da FPGA: eixos I/Q numéricos a 90,000°, círculo perfeito
    Resumo  - Comparação lado a lado

Modelo usado na Cena 2 (fator ½ do mixer; todo o erro de fase no LO de I):
    LO_I = cos(ωt − Δθ),   LO_Q = −(1+ε)·sin(ωt)
    I'_LPF = ½·I·cos Δθ − ½·Q·sin Δθ      <- diafonia: Q vaza para dentro de I
    Q'_LPF = ½·(1+ε)·Q
Geometricamente, I' é a projeção do fasor sobre um eixo de medição girado de
−Δθ; entre esse eixo e o eixo Q passam a existir 90° + Δθ.
"""

import shutil

import numpy as np
from manim import *

TEM_LATEX = shutil.which("latex") is not None and shutil.which("dvisvgm") is not None

# Paleta didática (fixa em todas as cenas)
COR_REAL = BLUE          # sinal real / ground truth
COR_REC = WHITE          # recuperado pelo DDC (coincide com o real)
COR_I = GOLD             # canal I
COR_Q = GREEN            # canal Q
COR_ERRO = RED           # distorções analógicas
COR_ERRO2 = ORANGE
COR_CHIP = PURPLE_B      # FPGA
COR_EIXO = GREY_B
FUNDO = "#0e1117"

# Erros "exagerados" para que a elipse fique visível na tela
DTH_EXAGERADO = 20.0     # graus
EPS_EXAGERADO = 0.30


# =============================================================================
# Utilitários de construção
# =============================================================================
def P(x, y):
    return np.array([x, y, 0.0])


def formula(tex, texto, cor=WHITE, tamanho=36):
    """Fórmula em MathTex se houver LaTeX; senão, Text com Unicode."""
    if TEM_LATEX:
        return MathTex(tex, color=cor, font_size=tamanho)
    return Text(texto, color=cor, font_size=tamanho * 0.8)


def formula_partes(partes, tamanho=36):
    """Fórmula multicolorida. partes = [(tex, texto_unicode, cor), ...]."""
    if TEM_LATEX:
        m = MathTex(*[p[0] for p in partes], font_size=tamanho)
        for sub, p in zip(m, partes):
            sub.set_color(p[2])
        return m
    markup = "".join(f'<span foreground="{ManimColor(c).to_hex()}">{t}</span>' for _, t, c in partes)
    return MarkupText(markup, font_size=tamanho * 0.8)


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
    caixa = RoundedRectangle(corner_radius=0.1, width=largura, height=altura,
                             color=cor, stroke_width=3)
    return VGroup(caixa, Text(rotulo, font_size=tamanho, color=cor).move_to(caixa))


def mixer(cor=WHITE, raio=0.32):
    c = Circle(radius=raio, color=cor, stroke_width=3)
    d = raio * 0.7
    x = VGroup(Line(P(-d, d), P(d, -d)), Line(P(-d, -d), P(d, d))).set_stroke(cor, 3)
    return VGroup(c, x)


def fio(pontos, cor, largura=4):
    """Polilinha terminada em seta (fiação dos diagramas de blocos)."""
    g = VGroup(*[Line(pontos[k], pontos[k + 1], color=cor, stroke_width=largura)
                 for k in range(len(pontos) - 2)])
    g.add(Arrow(pontos[-2], pontos[-1], buff=0, color=cor, stroke_width=largura,
                max_tip_length_to_length_ratio=0.3))
    return g


def caminho(pontos):
    return VMobject().set_points_as_corners(pontos)


def plano(centro, tam=5.6, alcance=1.4):
    eixos = Axes(x_range=[-alcance, alcance, 0.5], y_range=[-alcance, alcance, 0.5],
                 x_length=tam, y_length=tam,
                 axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO})
    eixos.move_to(centro)
    rot_i = Text("I", font_size=30, color=COR_I).next_to(eixos.x_axis.get_end(), DOWN, buff=0.15)
    rot_q = Text("Q", font_size=30, color=COR_Q).next_to(eixos.y_axis.get_end(), LEFT, buff=0.15)
    return eixos, VGroup(rot_i, rot_q)


def elipse_analogica(t, dth_graus, eps):
    """Ponto (I', Q') medido pelo demodulador analógico para z = e^{jt}."""
    d = np.deg2rad(dth_graus)
    i, q = np.cos(t), np.sin(t)
    return i * np.cos(d) - q * np.sin(d), (1 + eps) * q


# =============================================================================
# Cena
# =============================================================================
class IQDemodulationComparison(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_fasor()
        self.cena_analogica_esquema()
        self.cena_analogica_geometria()
        self.cena_ddc_esquema()
        self.cena_fpga()
        self.cena_resumo()

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
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        self.wait(0.2)

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Detecção I/Q em LLRF", font_size=56, weight=BOLD)
        sub = Text("Desmodulação analógica  ×  Amostragem digital (DDC)", font_size=30, color=GREY_A)
        ref = Text("Fig. 5(b)  ×  Fig. 5(c)", font_size=24, color=COR_EIXO)
        g = VGroup(titulo, sub, ref).arrange(DOWN, buff=0.35)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(ref, shift=UP * 0.2))
        self.wait(1.2)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_fasor(self):
        self.titulo_cena("1 · Fasor girante e decomposição I/Q")
        eixos, rotulos = plano(P(-3.5, -0.35))
        o = eixos.c2p(0, 0)
        s = ValueTracker(0.0)   # fase acumulada φ

        def amp(x):  # A(t): sobe de 0,35 a 1 na primeira volta (espiral), depois constante
            u = np.clip(x / TAU, 0, 1)
            return 0.35 + 0.65 * (3 * u**2 - 2 * u**3)

        def iq(x):
            return amp(x) * np.cos(x), amp(x) * np.sin(x)

        def ponta_pos():
            return eixos.c2p(*iq(s.get_value()))

        fasor = always_redraw(lambda: seta(o, ponta_pos(), COR_REAL, 7))
        seg_i = always_redraw(lambda: segmento(o, eixos.c2p(iq(s.get_value())[0], 0), COR_I, 9))
        seg_q = always_redraw(lambda: segmento(o, eixos.c2p(0, iq(s.get_value())[1]), COR_Q, 9))
        proj_i = always_redraw(lambda: tracejada(ponta_pos(), eixos.c2p(iq(s.get_value())[0], 0), COR_I))
        proj_q = always_redraw(lambda: tracejada(ponta_pos(), eixos.c2p(0, iq(s.get_value())[1]), COR_Q))
        arco = always_redraw(lambda: Arc(radius=0.45, start_angle=0,
                                         angle=max(s.get_value() % TAU, 0.02),
                                         arc_center=o, color=WHITE, stroke_width=2))
        rot_phi = formula(r"\varphi", "φ", WHITE, 30)
        rot_phi.add_updater(lambda m: m.move_to(
            o + 0.78 * np.array([np.cos((s.get_value() % TAU) / 2), np.sin((s.get_value() % TAU) / 2), 0])))
        rot_a = formula(r"A(t)", "A(t)", COR_REAL, 28)

        def pos_rot_a(m):
            x = s.get_value()
            normal = np.array([-np.sin(x), np.cos(x), 0])
            m.move_to((o + ponta_pos()) / 2 + 0.32 * normal)
        rot_a.add_updater(pos_rot_a)
        ponta = Dot(color=WHITE, radius=0.07).add_updater(lambda m: m.move_to(ponta_pos()))

        # Equações (direita, em cima)
        eqs = VGroup(
            formula(r"I(t) = A(t)\,\cos\varphi(t)", "I(t) = A(t)·cos φ(t)", COR_I, 38),
            formula(r"Q(t) = A(t)\,\sin\varphi(t)", "Q(t) = A(t)·sin φ(t)", COR_Q, 38),
            formula(r"z(t) = I + jQ = A\,e^{j\varphi}", "z(t) = I + jQ = A·e^(jφ)", WHITE, 38),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(P(3.5, 1.75))

        # Formas de onda I(t), Q(t) sendo desenhadas (direita, embaixo)
        ax_t = Axes(x_range=[0, 2 * TAU, PI / 2], y_range=[-1.2, 1.2, 0.5],
                    x_length=5.8, y_length=2.3,
                    axis_config={"include_tip": False, "stroke_width": 2, "color": COR_EIXO}
                    ).move_to(P(3.5, -1.55))
        rot_t = Text("fase acumulada φ →", font_size=18, color=COR_EIXO).next_to(ax_t, DOWN, buff=0.08)
        leg_t = VGroup(Text("I(t)", font_size=20, color=COR_I),
                       Text("Q(t)", font_size=20, color=COR_Q)).arrange(RIGHT, buff=0.3)
        leg_t.next_to(ax_t, UP, buff=0.05).align_to(ax_t, RIGHT)
        curva_i = always_redraw(lambda: ax_t.plot(lambda x: iq(x)[0],
                                                  x_range=[0, max(s.get_value(), 0.1), 0.04],
                                                  color=COR_I, stroke_width=3))
        curva_q = always_redraw(lambda: ax_t.plot(lambda x: iq(x)[1],
                                                  x_range=[0, max(s.get_value(), 0.1), 0.04],
                                                  color=COR_Q, stroke_width=3))
        ponto_i = always_redraw(lambda: Dot(ax_t.c2p(s.get_value(), iq(s.get_value())[0]),
                                            color=COR_I, radius=0.05))
        ponto_q = always_redraw(lambda: Dot(ax_t.c2p(s.get_value(), iq(s.get_value())[1]),
                                            color=COR_Q, radius=0.05))

        self.play(Create(eixos), FadeIn(rotulos), run_time=1.2)
        seta_inicial = seta(o, ponta_pos(), COR_REAL, 7)
        self.play(GrowArrow(seta_inicial), run_time=0.6)
        self.remove(seta_inicial)
        self.add(fasor, ponta)
        self.play(FadeIn(rot_a), Create(arco), FadeIn(rot_phi))
        leg = self.legenda("Um sinal de RF é um fasor: amplitude A(t) e fase φ(t)")
        self.play(Create(proj_i), Create(proj_q), Create(seg_i), Create(seg_q))
        self.play(Write(eqs[0]), Write(eqs[1]), run_time=1.5)
        leg = self.legenda("As projeções do fasor nos eixos SÃO as componentes I e Q", leg)
        self.play(Create(ax_t), FadeIn(rot_t), FadeIn(leg_t))
        self.add(curva_i, curva_q, ponto_i, ponto_q)

        rastro = TracedPath(ponta.get_center, stroke_color=BLUE_B, stroke_width=3)
        self.add(rastro)
        leg = self.legenda("A(t) crescendo (enchimento da cavidade): trajetória em espiral", leg)
        self.play(s.animate.set_value(TAU), run_time=6, rate_func=linear)
        leg = self.legenda("A(t) constante: o fasor descreve um círculo", leg)
        self.play(s.animate.set_value(2 * TAU), run_time=5, rate_func=linear)
        self.play(Write(eqs[2]))
        self.play(Indicate(eqs[2], color=COR_REAL))
        self.wait(1)
        self.limpar()

    # ================================================================= CENA 2a
    def cena_analogica_esquema(self):
        self.titulo_cena("2 · Desmodulação analógica direta (Fig. 5b)")
        yi, yq = 1.4, -1.4
        rf = bloco("RF", 0.9, 0.6, COR_REAL).move_to(P(-6.1, 0))
        div = bloco("Divisor", 1.3, 0.7).move_to(P(-4.3, 0))
        mx_i = mixer().move_to(P(-1.6, yi))
        mx_q = mixer().move_to(P(-1.6, yq))
        hib = bloco("90°", 0.9, 0.7).move_to(P(-1.6, 0))
        lo = bloco("LO", 0.9, 0.6).move_to(P(0.4, 0))
        lpf_i = bloco("LPF", 1.0, 0.6).move_to(P(1.0, yi))
        lpf_q = bloco("LPF", 1.0, 0.6).move_to(P(1.0, yq))
        tri = Triangle(color=WHITE, stroke_width=3).rotate(-PI / 2).scale(0.38).move_to(P(2.9, yq))
        rot_ganho = Text("ganho", font_size=18, color=WHITE).next_to(tri, DOWN, buff=0.12)
        out_i = Text("I'", font_size=36, color=COR_I).move_to(P(4.7, yi))
        out_q = Text("Q'", font_size=36, color=COR_Q).move_to(P(4.7, yq))

        w_rf = fio([rf.get_right(), div.get_left()], COR_REAL)
        fio_i = fio([div.get_top(), P(-4.3, yi), mx_i.get_left()], COR_I)
        fio_q = fio([div.get_bottom(), P(-4.3, yq), mx_q.get_left()], COR_Q)
        w_lo = fio([lo.get_left(), hib.get_right()], WHITE)
        w_hi = fio([hib.get_top(), mx_i.get_bottom()], WHITE, 3)
        w_hq = fio([hib.get_bottom(), mx_q.get_top()], WHITE, 3)
        w_i1 = fio([mx_i.get_right(), lpf_i.get_left()], COR_I)
        w_i2 = fio([lpf_i.get_right(), out_i.get_left() + LEFT * 0.15], COR_I)
        w_q1 = fio([mx_q.get_right(), lpf_q.get_left()], COR_Q)
        w_q2 = fio([lpf_q.get_right(), tri.get_left()], COR_Q)
        w_q3 = fio([tri.get_right(), out_q.get_left() + LEFT * 0.15], COR_Q)
        cab_i = Text("canal I (cobre)", font_size=20, color=COR_I).next_to(P(-3.0, yi), UP, buff=0.15)
        cab_q = Text("canal Q (cobre)", font_size=20, color=COR_Q).next_to(P(-3.0, yq), DOWN, buff=0.15)

        leg = self.legenda("O sinal de RF é dividido em dois canais físicos")
        self.play(FadeIn(rf), Create(w_rf), FadeIn(div))
        self.play(Create(fio_i), Create(fio_q), FadeIn(cab_i), FadeIn(cab_q),
                  FadeIn(mx_i), FadeIn(mx_q), run_time=1.5)
        leg = self.legenda("Um LO + híbrido de 90° geram as duas referências de fase", leg)
        self.play(FadeIn(lo), Create(w_lo), FadeIn(hib), Create(w_hi), Create(w_hq))
        self.play(Create(w_i1), FadeIn(lpf_i), Create(w_i2), Write(out_i),
                  Create(w_q1), FadeIn(lpf_q), Create(w_q2), Create(tri), FadeIn(rot_ganho),
                  Create(w_q3), Write(out_q), run_time=1.8)

        p_i = caminho([rf.get_right(), div.get_left(), div.get_top(), P(-4.3, yi), mx_i.get_left(),
                       mx_i.get_right(), lpf_i.get_left(), lpf_i.get_right(), out_i.get_left()])
        p_q = caminho([rf.get_right(), div.get_left(), div.get_bottom(), P(-4.3, yq), mx_q.get_left(),
                       mx_q.get_right(), lpf_q.get_left(), lpf_q.get_right(), out_q.get_left()])
        for _ in range(2):
            self.play(ShowPassingFlash(p_i.copy().set_stroke(WHITE, 7), time_width=0.4),
                      ShowPassingFlash(p_q.copy().set_stroke(WHITE, 7), time_width=0.4), run_time=1.4)

        # Imperfeição 1: erro de quadratura
        leg = self.legenda("Híbrido real: as referências ficam a 95° em vez de 90° (erro Δθ)", leg, COR_ERRO)
        novo = Text("95°", font_size=24, color=COR_ERRO).move_to(hib[1])
        self.play(hib[0].animate.set_color(COR_ERRO), Transform(hib[1], novo))
        self.play(Indicate(hib, color=COR_ERRO, scale_factor=1.3))
        # Imperfeição 2: desbalanço de ganho
        leg = self.legenda("Cabos, conectores e mixer de Q: ganho diferente (1+ε)", leg, COR_ERRO2)
        novo_g = Text("1+ε", font_size=22, color=COR_ERRO2).next_to(tri, DOWN, buff=0.12)
        self.play(tri.animate.set_color(COR_ERRO2), Transform(rot_ganho, novo_g))
        self.play(Indicate(VGroup(tri, rot_ganho), color=COR_ERRO2, scale_factor=1.3))
        leg = self.legenda("Dois caminhos físicos ⇒ erros diferentes em I e Q (que derivam com a temperatura)", leg)
        self.wait(1.5)
        self.limpar()

    # ================================================================= CENA 2b
    def cena_analogica_geometria(self):
        self.titulo_cena("2 · O que o hardware analógico faz com o fasor")
        eixos, rotulos = plano(P(-3.5, -0.35))
        o = eixos.c2p(0, 0)
        phi = ValueTracker(PI / 4)
        dth = ValueTracker(0.0)   # erro de quadratura [graus]
        eps = ValueTracker(0.0)   # desbalanço de ganho

        def u_i():  # direção do eixo de medição de I (girado de −Δθ)
            d = np.deg2rad(dth.get_value())
            return np.array([np.cos(d), -np.sin(d)])

        def real(f):
            return np.array([np.cos(f), np.sin(f)])

        def medido(f):
            return elipse_analogica(f, dth.get_value(), eps.get_value())

        circulo = ParametricFunction(lambda t: eixos.c2p(np.cos(t), np.sin(t)), t_range=[0, TAU],
                                     color=COR_REAL, stroke_width=5)
        fasor = always_redraw(lambda: seta(o, eixos.c2p(*real(phi.get_value())), COR_REAL, 6))
        eixo_med = always_redraw(lambda: DashedLine(eixos.c2p(*(-1.35 * u_i())), eixos.c2p(*(1.35 * u_i())),
                                                    color=COR_ERRO, stroke_width=3, dash_length=0.12))
        rot_eixo = always_redraw(lambda: Text("eixo I medido", font_size=18, color=COR_ERRO)
                                 .next_to(eixos.c2p(*(1.3 * u_i())), DOWN, buff=0.12))
        arco = always_redraw(lambda: Arc(radius=0.6, start_angle=-np.deg2rad(dth.get_value()),
                                         angle=PI / 2 + np.deg2rad(dth.get_value()),
                                         arc_center=o, color=COR_ERRO2, stroke_width=3))

        def txt_angulo():
            meio = (PI / 2 - np.deg2rad(dth.get_value())) / 2
            return Text(f"{90 + dth.get_value():.1f}°", font_size=22, color=COR_ERRO2).move_to(
                o + 1.05 * np.array([np.cos(meio), np.sin(meio), 0]))
        rot_ang = always_redraw(txt_angulo)

        def pe_projecao():
            z = real(phi.get_value())
            return eixos.c2p(*(np.dot(z, u_i()) * u_i()))
        proj = always_redraw(lambda: tracejada(eixos.c2p(*real(phi.get_value())), pe_projecao(), COR_ERRO2, 3))
        pe = always_redraw(lambda: Dot(pe_projecao(), color=COR_ERRO2, radius=0.06))
        elipse = always_redraw(lambda: ParametricFunction(lambda t: eixos.c2p(*medido(t)),
                                                          t_range=[0, TAU, 0.02],
                                                          color=COR_ERRO, stroke_width=4))
        fasor_med = always_redraw(lambda: seta(o, eixos.c2p(*medido(phi.get_value())), COR_ERRO2, 5))

        # Fórmulas (direita)
        f_lo = VGroup(
            formula(r"\mathrm{LO}_I = \cos(\omega t - \Delta\theta)", "LO_I = cos(ωt − Δθ)", COR_I, 30),
            formula(r"\mathrm{LO}_Q = -(1+\varepsilon)\,\sin(\omega t)", "LO_Q = −(1+ε)·sin(ωt)", COR_Q, 30),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(P(3.5, 2.05))
        f_i = formula_partes([(r"I'_{\mathrm{LPF}} = \tfrac{1}{2}\,I\cos\Delta\theta", "I'_LPF = ½·I·cos Δθ ", COR_I),
                              (r"-\,\tfrac{1}{2}\,Q\sin\Delta\theta", "− ½·Q·sin Δθ", COR_ERRO)], 38)
        f_i.move_to(P(3.5, 0.85))
        f_q = formula_partes([(r"Q'_{\mathrm{LPF}} = \tfrac{1}{2}", "Q'_LPF = ½·", COR_Q),
                              (r"(1+\varepsilon)", "(1+ε)", COR_ERRO2),
                              (r"\,Q", "·Q", COR_Q)], 38)
        f_q.move_to(P(3.5, -0.45))
        termo_erro = f_i[1] if TEM_LATEX else f_i
        leituras = always_redraw(lambda: VGroup(
            Text(f"Δθ = {dth.get_value():4.1f}°", font_size=22, color=COR_ERRO),
            Text(f"ε = {eps.get_value():.2f}", font_size=22, color=COR_ERRO2),
            Text(f"fuga Q→I = {100 * np.tan(np.deg2rad(dth.get_value())):.1f}%", font_size=22, color=GREY_A),
        ).arrange(RIGHT, buff=0.45).move_to(P(3.5, -1.35)))

        # 1) Situação ideal
        self.play(Create(eixos), FadeIn(rotulos), Create(circulo), run_time=1.2)
        self.add(fasor)
        leg = self.legenda("Ideal: eixos de medição a 90° ⇒ a medida reproduz o círculo")
        self.play(FadeIn(eixo_med), FadeIn(rot_eixo), Create(arco), FadeIn(rot_ang))
        self.add(elipse, fasor_med)
        self.play(phi.animate.increment_value(TAU / 2), run_time=2.5, rate_func=linear)
        self.play(Write(f_lo), run_time=1.2)
        self.play(Write(f_i), Write(f_q), run_time=1.5)
        self.play(FadeIn(leituras))

        # 2) Erro realista: 95°
        leg = self.legenda("Híbrido a 95°: o eixo de medição de I inclina 5°", leg, COR_ERRO)
        self.play(dth.animate.set_value(5.0), phi.animate.increment_value(TAU / 4),
                  run_time=2.5, rate_func=smooth)
        leg = self.legenda("I' é a projeção no eixo inclinado: um pedaço de Q entra em I", leg, COR_ERRO2)
        self.play(Create(proj), FadeIn(pe))
        self.play(phi.animate.increment_value(TAU / 2), run_time=3, rate_func=linear)
        caixa = SurroundingRectangle(termo_erro, color=COR_ERRO, buff=0.1)
        rot_cx = Text("diafonia: Q vaza para I (erro de fase residual)", font_size=20,
                      color=COR_ERRO).next_to(caixa, DOWN, buff=0.1)
        self.play(Create(caixa), FadeIn(rot_cx))
        self.play(Indicate(termo_erro, color=COR_ERRO, scale_factor=1.15))

        # 3) Erros exagerados para tornar a elipse visível
        leg = self.legenda(f"Exagerando (Δθ = {DTH_EXAGERADO:.0f}°, ε = {EPS_EXAGERADO:.0%}): "
                           "o círculo vira uma elipse inclinada", leg, COR_ERRO)
        self.play(dth.animate.set_value(DTH_EXAGERADO), eps.animate.set_value(EPS_EXAGERADO),
                  phi.animate.increment_value(TAU / 4), run_time=3, rate_func=smooth)
        self.play(phi.animate.increment_value(TAU), run_time=5, rate_func=linear)

        imagem = VGroup(
            formula(r"z' = \alpha\,z + \beta\,z^{*}", "z' = α·z + β·z*", WHITE, 34),
            Text("β·z*: termo-imagem ⇒ elipse.\nNão se corrige com um único ganho/fase.",
                 font_size=20, color=GREY_A),
        ).arrange(DOWN, buff=0.15).move_to(P(3.5, -2.45))
        leg = self.legenda("A medida mistura I e Q: o vetor medido não acompanha o vetor real", leg)
        self.play(FadeIn(imagem, shift=UP * 0.2))
        self.play(Indicate(elipse, color=COR_ERRO), phi.animate.increment_value(TAU / 2),
                  run_time=2.5, rate_func=linear)
        self.wait(1.5)
        self.limpar()

    # ================================================================= CENA 3a
    def cena_ddc_esquema(self):
        self.titulo_cena("3 · Arquitetura digital: IF + DDC (Fig. 5c)")
        y0 = 1.85
        rf = bloco("RF", 0.9, 0.6, COR_REAL, 22).move_to(P(-6.2, y0))
        mx = mixer().move_to(P(-4.7, y0))
        lo = bloco("LO", 0.8, 0.5, WHITE, 20).move_to(P(-4.7, y0 - 1.1))
        aa = bloco("LPF", 0.9, 0.6, WHITE, 22).move_to(P(-3.0, y0))
        adc = bloco("ADC", 0.9, 0.6, WHITE, 22).move_to(P(-1.35, y0))
        chip = RoundedRectangle(corner_radius=0.2, width=5.7, height=2.2, color=COR_CHIP,
                                stroke_width=4).move_to(P(3.45, y0 - 0.1))
        rot_chip = Text("FPGA", font_size=22, color=COR_CHIP, weight=BOLD).next_to(
            chip.get_corner(UL), DR, buff=0.12)
        ya, yb = y0 + 0.35, y0 - 0.6
        m_i = mixer(COR_I, 0.25).move_to(P(2.3, ya))
        m_q = mixer(COR_Q, 0.25).move_to(P(2.3, yb))
        nco_i = Text("cos[n]", font_size=16, color=COR_I).next_to(m_i, RIGHT, buff=0.1).shift(UP * 0.25)
        nco_q = Text("−sin[n]", font_size=16, color=COR_Q).next_to(m_q, RIGHT, buff=0.1).shift(DOWN * 0.25)
        fir_i = bloco("FIR", 0.8, 0.42, COR_I, 18).move_to(P(4.1, ya))
        fir_q = bloco("FIR", 0.8, 0.42, COR_Q, 18).move_to(P(4.1, yb))
        o_i = Text("I", font_size=28, color=COR_I).move_to(P(5.75, ya))
        o_q = Text("Q", font_size=28, color=COR_Q).move_to(P(5.75, yb))
        no = Dot(P(1.3, y0 - 0.12), radius=0.06, color=WHITE)

        w1 = fio([rf.get_right(), mx.get_left()], COR_REAL)
        w_lo = fio([lo.get_top(), mx.get_bottom()], WHITE, 3)
        w2 = fio([mx.get_right(), aa.get_left()], COR_REAL)
        w3 = fio([aa.get_right(), adc.get_left()], COR_REAL)
        w4 = fio([adc.get_right(), P(1.3, y0 - 0.12) + LEFT * 0.06], WHITE)
        wi = VGroup(fio([no.get_center(), P(1.3, ya), m_i.get_left()], WHITE, 3),
                    fio([m_i.get_right(), fir_i.get_left()], COR_I, 3),
                    fio([fir_i.get_right(), o_i.get_left() + LEFT * 0.1], COR_I, 3))
        wq = VGroup(fio([no.get_center(), P(1.3, yb), m_q.get_left()], WHITE, 3),
                    fio([m_q.get_right(), fir_q.get_left()], COR_Q, 3),
                    fio([fir_q.get_right(), o_q.get_left() + LEFT * 0.1], COR_Q, 3))
        n1 = Text("(1) 1 mixer", font_size=18, color=GREY_A).next_to(mx, UP, buff=0.2)
        n_if = Text("IF = 20 MHz", font_size=16, color=COR_REAL).next_to(w2, DOWN, buff=0.12)
        n2 = Text("(2) 1 ADC", font_size=18, color=GREY_A).next_to(adc, UP, buff=0.2)
        n3 = Text("(3) processamento numérico", font_size=18, color=GREY_A).next_to(chip, UP, buff=0.1)

        leg = self.legenda("1) Um ÚNICO mixer desce a portadora para a IF (20 MHz)")
        self.play(FadeIn(rf), Create(w1), FadeIn(mx), FadeIn(lo), Create(w_lo), FadeIn(n1))
        self.play(Create(w2), FadeIn(n_if), FadeIn(aa), Create(w3))
        leg = self.legenda("2) Um ÚNICO ADC digitaliza a IF: um só caminho analógico", leg)
        self.play(FadeIn(adc), FadeIn(n2))
        leg = self.legenda("3) I e Q são separados dentro da FPGA, por aritmética", leg)
        self.play(Create(chip), FadeIn(rot_chip), FadeIn(n3), Create(w4), FadeIn(no))
        self.play(Create(wi), Create(wq), FadeIn(m_i), FadeIn(m_q), FadeIn(nco_i), FadeIn(nco_q),
                  FadeIn(fir_i), FadeIn(fir_q), Write(o_i), Write(o_q), run_time=1.6)
        p_rf = caminho([rf.get_right(), mx.get_left(), mx.get_right(), aa.get_left(), aa.get_right(),
                        adc.get_left(), adc.get_right(), no.get_center()])
        self.play(ShowPassingFlash(p_rf.set_stroke(WHITE, 7), time_width=0.5), run_time=1.3)

        # Amostragem síncrona da IF
        ax_w = Axes(x_range=[0, 3, 0.25], y_range=[-1.3, 1.3, 0.5], x_length=11.5, y_length=2.5,
                    axis_config={"include_tip": False, "stroke_width": 2, "color": COR_EIXO}
                    ).move_to(P(0, -1.75))
        fase0 = np.deg2rad(40)  # φ = 40°: I e Q ambos não nulos
        onda = ax_w.plot(lambda x: np.cos(TAU * x + fase0), x_range=[0, 3, 0.005],
                         color=COR_REAL, stroke_width=4)
        rot_onda = Text("IF analógica (20 MHz)", font_size=20, color=COR_REAL).next_to(
            ax_w, UP, buff=0.0).align_to(ax_w, LEFT)
        rot_tempo = Text("tempo (períodos de IF) →", font_size=18, color=COR_EIXO).next_to(
            ax_w, DOWN, buff=0.05).align_to(ax_w, RIGHT)

        leg = self.legenda("A senoide em IF contínua, vinda do mixer", leg)
        self.play(Create(ax_w), FadeIn(rot_onda), FadeIn(rot_tempo))
        self.play(Create(onda), run_time=2)

        xs = np.arange(13) / 4
        pontos = [ax_w.c2p(x, np.cos(TAU * x + fase0)) for x in xs]
        hastes = VGroup(*[Line(ax_w.c2p(x, 0), p, color=GREY_B, stroke_width=2) for x, p in zip(xs, pontos)])
        amostras = VGroup(*[Dot(p, radius=0.08, color=WHITE) for p in pontos])
        nomes = ["I", "−Q", "−I", "+Q"]
        cores = [COR_I, COR_Q, COR_I, COR_Q]
        rotulos = VGroup()
        for k in range(12):
            y = np.cos(TAU * xs[k] + fase0)
            rotulos.add(Text(nomes[k % 4], font_size=20, color=cores[k % 4], weight=BOLD)
                        .next_to(pontos[k], UP if y >= 0 else DOWN, buff=0.12))
        leg = self.legenda("f_s = 4·f_IF = 80 MSPS: cada amostra avança exatamente 90° na fase da IF", leg)
        self.play(LaggedStart(*[AnimationGroup(Create(h), GrowFromCenter(d))
                                for h, d in zip(hastes, amostras)], lag_ratio=0.15), run_time=2.5)
        leg = self.legenda("As amostras valem I, −Q, −I, +Q, …  (a quadratura vem do RELÓGIO)", leg)
        self.play(LaggedStart(*[FadeIn(r, shift=UP * 0.1) for r in rotulos], lag_ratio=0.12), run_time=2)
        self.wait(1)

        leg = self.legenda("As amostras entram na FPGA como números", leg)
        self.play(LaggedStart(*[FadeOut(d.copy(), target_position=no.get_center(), scale=0.3)
                                for d in amostras], lag_ratio=0.08), run_time=2.2)
        self.play(*[ShowPassingFlash(caminho([no.get_center(), P(1.3, y), P(5.5, y)]).set_stroke(c, 6),
                                     time_width=0.5) for y, c in [(ya, COR_I), (yb, COR_Q)]],
                  run_time=1.2)
        self.wait(0.8)
        self.limpar()

    # ================================================================= CENA 3b
    def cena_fpga(self):
        self.titulo_cena("3 · Dentro da FPGA: quadratura numérica")
        moldura = RoundedRectangle(corner_radius=0.3, width=13.4, height=6.0, color=COR_CHIP,
                                   stroke_width=4).move_to(P(0, -0.5))
        rot_m = Text("FPGA", font_size=22, color=COR_CHIP, weight=BOLD).next_to(
            moldura.get_corner(UL), DR, buff=0.15)
        self.play(Create(moldura), FadeIn(rot_m))

        codigo = VGroup(*[Text(l, font="Monospace", font_size=19, color=c) for l, c in [
            ("// NCO com f_s = 4·f_IF", GREY_B),
            ("cos_lut[4] = { 1, 0, -1,  0 }", COR_I),
            ("sin_lut[4] = { 0, 1,  0, -1 }", COR_Q),
            ("I[n] =  x[n] · cos_lut[n % 4]", COR_I),
            ("Q[n] = -x[n] · sin_lut[n % 4]", COR_Q),
            ("// + filtro FIR passa-baixas", GREY_B),
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(P(-3.3, 0.85))
        leg = self.legenda("Os osciladores I e Q são tabelas de números exatos: sem cobre, sem drift")
        self.play(LaggedStart(*[Write(l) for l in codigo], lag_ratio=0.3), run_time=3)

        eixos, _ = plano(P(3.4, -0.55), 4.9)
        eixos.set_opacity(0.35)
        o = eixos.c2p(0, 0)
        eixo_i = Arrow(eixos.c2p(-1.35, 0), eixos.c2p(1.35, 0), buff=0, color=COR_I, stroke_width=5,
                       max_tip_length_to_length_ratio=0.06)
        eixo_q = Arrow(eixos.c2p(0, -1.35), eixos.c2p(0, 1.35), buff=0, color=COR_Q, stroke_width=5,
                       max_tip_length_to_length_ratio=0.06)
        r_i = Text("I", font_size=28, color=COR_I).next_to(eixo_i.get_end(), DOWN, buff=0.12)
        r_q = Text("Q", font_size=28, color=COR_Q).next_to(eixo_q.get_end(), LEFT, buff=0.12)
        angulo_reto = RightAngle(Line(o, eixos.c2p(1, 0)), Line(o, eixos.c2p(0, 1)), length=0.35,
                                 color=WHITE, stroke_width=3)
        rot_90 = Text("90,000°", font_size=24, color=WHITE, weight=BOLD).next_to(
            angulo_reto, UR, buff=0.08)

        self.play(FadeIn(eixos))
        leg = self.legenda("Eixos I e Q gerados por matemática: ortogonais por definição", leg)
        self.play(GrowArrow(eixo_i), FadeIn(r_i))
        self.play(GrowArrow(eixo_q), FadeIn(r_q))
        self.play(Create(angulo_reto), Write(rot_90))
        self.play(Indicate(rot_90, color=WHITE, scale_factor=1.3))

        leituras = VGroup(
            Text("Δθ = 0,000°   (exato)", font_size=22, color=COR_REC),
            Text("ε = 0   (I e Q vêm do mesmo ADC)", font_size=22, color=COR_REC),
            Text("diafonia I↔Q = 0   ·   IRR → ∞", font_size=22, color=COR_REC),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(P(-3.3, -1.95))
        self.play(LaggedStart(*[FadeIn(l, shift=RIGHT * 0.2) for l in leituras], lag_ratio=0.3))

        # Fasor e trajetória recuperados
        phi = ValueTracker(0.0)
        fantasma = DashedVMobject(ParametricFunction(
            lambda t: eixos.c2p(*elipse_analogica(t, DTH_EXAGERADO, EPS_EXAGERADO)),
            t_range=[0, TAU, 0.02], color=COR_ERRO, stroke_width=2), num_dashes=60).set_opacity(0.55)
        rot_fant = Text("analógico (referência)", font_size=16, color=COR_ERRO).next_to(
            eixos.c2p(0.55, -1.35), DOWN, buff=0.02)
        circulo = ParametricFunction(lambda t: eixos.c2p(np.cos(t), np.sin(t)), t_range=[0, TAU],
                                     color=COR_REAL, stroke_width=9)
        fasor = always_redraw(lambda: seta(o, eixos.c2p(np.cos(phi.get_value()), np.sin(phi.get_value())),
                                           COR_REAL, 7))
        ponta = Dot(radius=0.07, color=COR_REC).add_updater(
            lambda m: m.move_to(eixos.c2p(np.cos(phi.get_value()), np.sin(phi.get_value()))))

        leg = self.legenda("Real (azul) × recuperado pelo DDC (branco)", leg)
        self.play(Create(fantasma), FadeIn(rot_fant), Create(circulo), run_time=1.5)
        self.add(fasor, ponta)
        rastro = TracedPath(ponta.get_center, stroke_color=COR_REC, stroke_width=3)
        self.add(rastro)
        self.play(phi.animate.set_value(TAU), run_time=5, rate_func=linear)

        amostras = VGroup(*[Dot(eixos.c2p(np.cos(a), np.sin(a)), radius=0.06, color=COR_REC)
                            for a in np.linspace(0, TAU, 24, endpoint=False)])
        leg = self.legenda("Cada amostra I[n] + jQ[n] cai exatamente sobre o círculo real", leg)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in amostras], lag_ratio=0.08), run_time=2)
        self.play(Indicate(circulo, color=COR_REC, scale_factor=1.05))
        leg = self.legenda("Sem elipse, sem descasamento de amplitude: recuperação perfeita", leg, COR_REC)
        self.wait(1.5)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo")
        lados = [
            (-3.5, "Analógico (Zero-IF)", COR_ERRO,
             "• 2 caminhos de cobre\n• Δθ, ε, offset DC\n• diafonia I ↔ Q, elipse"),
            (3.5, "Digital (IF + DDC)", COR_REC,
             "• 1 caminho analógico\n• quadratura numérica 90,000°\n• I e Q sem descasamento"),
        ]
        grupos = []
        for x, nome, cor, texto in lados:
            eixos, rot = plano(P(x, 0.25), 4.0)
            circ = ParametricFunction(lambda t, e=eixos: e.c2p(np.cos(t), np.sin(t)), t_range=[0, TAU],
                                      color=COR_REAL, stroke_width=7)
            if cor == COR_ERRO:
                medida = ParametricFunction(
                    lambda t, e=eixos: e.c2p(*elipse_analogica(t, DTH_EXAGERADO, EPS_EXAGERADO)),
                    t_range=[0, TAU, 0.02], color=COR_ERRO, stroke_width=4)
            else:
                medida = ParametricFunction(lambda t, e=eixos: e.c2p(np.cos(t), np.sin(t)),
                                            t_range=[0, TAU], color=COR_REC, stroke_width=2.5)
            cab = Text(nome, font_size=28, color=cor, weight=BOLD).next_to(eixos, UP, buff=0.1)
            itens = Text(texto, font_size=20, color=GREY_A, line_spacing=1.1).next_to(eixos, DOWN, buff=0.15)
            grupos.append((eixos, rot, circ, medida, cab, itens))

        for eixos, rot, circ, medida, cab, itens in grupos:
            self.play(FadeIn(cab), Create(eixos), FadeIn(rot), Create(circ), run_time=1)
            self.play(Create(medida), FadeIn(itens, shift=UP * 0.15), run_time=1.5)
        nota = Text(f"(erros analógicos exagerados: Δθ = {DTH_EXAGERADO:.0f}°, ε = {EPS_EXAGERADO:.0%})",
                    font_size=16, color=COR_EIXO).to_corner(UR, buff=0.45)
        self.play(FadeIn(nota))
        final = Text("Por isso LLRFs modernos, como o do Sirius, fazem a detecção I/Q no digital",
                     font_size=24, color=WHITE).to_edge(DOWN, buff=0.3)
        self.play(Write(final), run_time=2)
        self.play(Indicate(grupos[1][3], color=COR_REC))
        self.wait(2.5)
        self.limpar()
