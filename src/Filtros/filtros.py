# -*- coding: utf-8 -*-
"""
Filtros de 1ª e 2ª ordem: ordem, roll-off, ressonância e o RLC
==============================================================

Renderização (a partir da raiz do repositório):
    manim -pql src/Filtros/filtros.py Filtros   # rascunho
    manim -pqh src/Filtros/filtros.py Filtros   # final

Requer LaTeX (MathTex).

Roteiro (segue "docs/Filtros"):
    Abertura
    Cena 1 - Ordem de um filtro: grau de D(s) = nº de polos = nº de elementos reativos
    Cena 2 - Roll-off: −20 dB/década (1ª ordem) × −40 dB/década (2ª ordem)
    Cena 3 - Comportamento dinâmico: polos no plano s e resposta ao degrau (ζ, Q)
    Cena 4 - 1ª ordem: passa-baixa (tensão no C) e passa-alta (tensão no R)
    Cena 5 - 2ª ordem: mesmo denominador; o numerador define LP, BP ou HP
    Cena 6 - Um RLC série, quatro filtros: V_C, V_L, V_R e V_LC
    Cena 7 - RLC série × RLC paralelo: impedância mínima × máxima na ressonância
    Resumo

Diagramas de Bode em frequência normalizada (ω/ω0 ou ω/ωc), escala log.
"""

import numpy as np
from manim import *

# Paleta didática (fixa em todas as cenas)
COR_LP = BLUE            # passa-baixa
COR_HP = ORANGE          # passa-alta
COR_BP = GREEN           # passa-banda
COR_NOTCH = PURPLE_B     # rejeita-banda
COR_R = GREY_A           # resistor
COR_L = TEAL             # indutor
COR_C = GOLD             # capacitor
COR_FONTE = WHITE
COR_DESTAQUE = YELLOW
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}


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


def eixos_tempo(centro, largura, altura, x_range, y_range):
    return Axes(x_range=x_range, y_range=y_range, x_length=largura, y_length=altura,
                axis_config=EIXO_CFG).move_to(centro)


def rotulo_eixo(ax, mob):
    """Coloca um rótulo acima do canto esquerdo de um eixo."""
    return mob.next_to(ax, UP, buff=0.04).align_to(ax, LEFT)


# ------------------------------------------------------------ símbolos de circuito
def _colocar(g, a, b):
    """Leva um símbolo desenhado sobre o eixo x local (de 0 a |b − a|) para o segmento a → b."""
    d = b - a
    g.rotate(np.arctan2(d[1], d[0]), about_point=ORIGIN)
    g.shift(a)
    return g


def fio(pontos, cor=WHITE, largura=4):
    return VMobject().set_points_as_corners(pontos).set_stroke(cor, largura)


def resistor(a, b, cor=COR_R, largura=4):
    L = np.linalg.norm(b - a)
    m, h = L / 2, 0.3
    pts = [P(0, 0), P(m - h, 0)]
    for k in range(6):
        pts.append(P(m - h + (k + 0.5) * 2 * h / 6, 0.13 if k % 2 == 0 else -0.13))
    pts += [P(m + h, 0), P(L, 0)]
    return _colocar(VGroup(VMobject().set_points_as_corners(pts).set_stroke(cor, largura)), a, b)


def capacitor(a, b, cor=COR_C, largura=4):
    L = np.linalg.norm(b - a)
    m, g = L / 2, 0.08
    partes = VGroup(Line(P(0, 0), P(m - g, 0)), Line(P(m - g, -0.28), P(m - g, 0.28)),
                    Line(P(m + g, -0.28), P(m + g, 0.28)), Line(P(m + g, 0), P(L, 0)))
    return _colocar(partes.set_stroke(cor, largura), a, b)


def indutor(a, b, cor=COR_L, largura=4, voltas=4, r=0.09):
    L = np.linalg.norm(b - a)
    x0 = L / 2 - voltas * r
    partes = VGroup(Line(P(0, 0), P(x0, 0)))
    for k in range(voltas):
        partes.add(Arc(radius=r, start_angle=PI, angle=-PI, arc_center=P(x0 + r + 2 * r * k, 0)))
    partes.add(Line(P(L / 2 + voltas * r, 0), P(L, 0)))
    return _colocar(partes.set_stroke(cor, largura), a, b)


def fonte(a, b, cor=COR_FONTE, largura=4, raio=0.3):
    """Fonte senoidal (círculo com ~) entre a e b."""
    L = np.linalg.norm(b - a)
    g = _colocar(VGroup(Line(P(0, 0), P(L / 2 - raio, 0)), Circle(radius=raio).move_to(P(L / 2, 0)),
                        Line(P(L / 2 + raio, 0), P(L, 0))).set_stroke(cor, largura), a, b)
    seno = ParametricFunction(lambda t: P(t, 0.09 * np.sin(PI * t / 0.16)), t_range=[-0.16, 0.16],
                              color=cor, stroke_width=3).move_to((a + b) / 2)
    return VGroup(g, seno)


# ------------------------------------------------------------ diagramas de Bode
def eixos_bode(centro, largura=6.0, altura=3.0, db=(-60, 20), passo=20, rotulo="ω/ω₀"):
    ax = Axes(x_range=[-2, 2, 1], y_range=[db[0], db[1], passo], x_length=largura, y_length=altura,
              axis_config=EIXO_CFG).move_to(centro)
    rx = VGroup(*[Text(t, font_size=16, color=COR_EIXO).next_to(ax.c2p(x, db[0]), DOWN, buff=0.1)
                  for x, t in zip(range(-2, 3), ["0,01", "0,1", "1", "10", "100"])])
    ry = VGroup(*[Text(f"{v}", font_size=16, color=COR_EIXO).next_to(ax.c2p(-2, v), LEFT, buff=0.1)
                  for v in range(db[0], db[1] + 1, passo)])
    nome_x = Text(f"{rotulo}  (escala log)", font_size=16, color=COR_EIXO).next_to(rx, DOWN, buff=0.08
                                                                                   ).align_to(ax, RIGHT)
    nome_y = Text("dB", font_size=16, color=COR_EIXO).next_to(ax.c2p(-2, db[1]), UP, buff=0.1)
    grade = VGroup(*[DashedLine(ax.c2p(x, db[0]), ax.c2p(x, db[1]), color=GREY_D, stroke_width=1)
                     for x in range(-2, 3)])
    return ax, VGroup(grade, rx, ry, nome_x, nome_y)


def ganho_db(H, x, db=(-60, 20)):
    v = abs(H(1j * 10 ** x))
    return float(np.clip(20 * np.log10(max(v, 1e-12)), db[0], db[1]))


def curva_bode(ax, H, cor, db=(-60, 20), largura=4):
    return ax.plot(lambda x: ganho_db(H, x, db), x_range=[-2, 2, 0.005], color=cor, stroke_width=largura)


def degrau_2a(t, zeta):
    """Resposta ao degrau de ω0²/(s² + 2ζω0 s + ω0²), ω0 = 1."""
    z = zeta if abs(zeta - 1) > 1e-3 else 1.001
    r = np.sqrt(complex(z * z - 1))
    p1, p2 = -z + r, -z - r
    return float(np.real(1 + (p2 * np.exp(p1 * t) - p1 * np.exp(p2 * t)) / (p1 - p2)))


# =============================================================================
# Cena
# =============================================================================
class Filtros(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_ordem()
        self.cena_rolloff()
        self.cena_dinamica()
        self.cena_primeira_ordem()
        self.cena_segunda_ordem()
        self.cena_tabela_segunda()
        self.cena_rlc_serie()
        self.cena_serie_paralelo()
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

    def malha(self, x0, x1, y0, y1, topo, direita, esquerda):
        """Malha retangular: 'esquerda' e 'direita' são construtores (a, b) de um componente
        em cada lateral; 'topo' é uma lista [(nome, construtor, fração_ini, fração_fim), ...]."""
        TL, TR, BR, BL = P(x0, y1), P(x1, y1), P(x1, y0), P(x0, y0)
        partes = VGroup()
        comps = {}
        comps["esq"] = esquerda(TL, BL)
        comps["dir"] = direita(TR, BR)
        x_atual = x0
        for nome, construtor, fi, ff in topo:
            xa, xb = x0 + fi * (x1 - x0), x0 + ff * (x1 - x0)
            if xa > x_atual + 1e-6:
                partes.add(fio([P(x_atual, y1), P(xa, y1)]))
            comps[nome] = construtor(P(xa, y1), P(xb, y1))
            x_atual = xb
        if x_atual < x1 - 1e-6:
            partes.add(fio([P(x_atual, y1), P(x1, y1)]))
        partes.add(fio([BR, BL]))
        return partes, comps

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Filtros", font_size=64, weight=BOLD)
        sub = Text("Ordem, roll-off, ressonância e o circuito RLC", font_size=30, color=GREY_A)
        ax, deco = eixos_bode(P(0, 0), 5.0, 1.6, (-60, 20))
        curvas = VGroup(
            curva_bode(ax, lambda s: 1 / (s * s + s / 0.707 + 1), COR_LP, largura=3),
            curva_bode(ax, lambda s: (s / 2) / (s * s + s / 2 + 1), COR_BP, largura=3),
            curva_bode(ax, lambda s: s * s / (s * s + s / 0.707 + 1), COR_HP, largura=3),
        )
        g = VGroup(titulo, sub, VGroup(ax, curvas)).arrange(DOWN, buff=0.4)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2))
        self.play(Create(ax), LaggedStart(*[Create(c) for c in curvas], lag_ratio=0.3), run_time=2)
        self.wait(1)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_ordem(self):
        self.titulo_cena("1 · Ordem de um filtro")
        h = tex(r"H(s) = \frac{N(s)}{D(s)}", WHITE, 40).move_to(P(0, 2.45))
        regra = Text("ordem = grau de D(s) = nº de polos = nº de elementos que armazenam energia",
                     font_size=22, color=COR_DESTAQUE).move_to(P(0, 1.55))

        fio_rc, rc = self.malha(-5.6, -2.0, -0.9, 0.7,
                                [("R", resistor, 0.25, 0.75)], capacitor, fonte)
        fio_rlc, rlc = self.malha(1.6, 5.6, -0.9, 0.7,
                                  [("R", resistor, 0.12, 0.47), ("L", indutor, 0.53, 0.88)], capacitor, fonte)
        rotulos = VGroup(
            tex("R", COR_R, 28).next_to(rc["R"], UP, buff=0.15),
            tex("C", COR_C, 28).next_to(rc["dir"], RIGHT, buff=0.15),
            tex("R", COR_R, 28).next_to(rlc["R"], UP, buff=0.15),
            tex("L", COR_L, 28).next_to(rlc["L"], UP, buff=0.15),
            tex("C", COR_C, 28).next_to(rlc["dir"], RIGHT, buff=0.15),
        )
        f1 = tex(r"H(s) = \frac{N(s)}{a_1 s + a_0}", WHITE, 32).move_to(P(-3.8, -1.85))
        f2 = tex(r"H(s) = \frac{N(s)}{b_2 s^2 + b_1 s + b_0}", WHITE, 32).move_to(P(3.6, -1.85))
        n1 = Text("1 elemento reativo · 1 polo · 1ª ordem", font_size=20, color=COR_C).next_to(f1, DOWN, buff=0.15)
        n2 = Text("2 elementos reativos · 2 polos · 2ª ordem", font_size=20, color=COR_L).next_to(f2, DOWN, buff=0.15)

        leg = self.legenda("Todo filtro linear é descrito por uma função de transferência H(s)")
        self.play(Write(h))
        self.play(FadeIn(regra, shift=UP * 0.1))
        leg = self.legenda("Em circuitos passivos: conte capacitores e indutores independentes", leg)
        self.play(Create(fio_rc), *[Create(c) for c in rc.values()], run_time=1.5)
        self.play(Create(fio_rlc), *[Create(c) for c in rlc.values()], run_time=1.5)
        self.play(FadeIn(rotulos))
        self.play(Indicate(rc["dir"], color=COR_DESTAQUE, scale_factor=1.3))
        self.play(Write(f1), FadeIn(n1))
        self.play(Indicate(rlc["L"], color=COR_DESTAQUE, scale_factor=1.3),
                  Indicate(rlc["dir"], color=COR_DESTAQUE, scale_factor=1.3))
        self.play(Write(f2), FadeIn(n2))
        leg = self.legenda("Maior potência de s no denominador = ordem da equação diferencial do circuito", leg)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 2
    def cena_rolloff(self):
        self.titulo_cena("2 · Taxa de atenuação (roll-off)")
        db = (-80, 20)
        ax, deco = eixos_bode(P(0.5, -0.2), 10.5, 4.6, db, rotulo="ω/ωc")
        h1 = lambda s: 1 / (s + 1)
        h2 = lambda s: 1 / (s * s + s / 0.707 + 1)
        c1 = curva_bode(ax, h1, COR_C, db)
        c2 = curva_bode(ax, h2, COR_L, db)
        r1 = Text("1ª ordem (RC)", font_size=20, color=COR_C).next_to(ax.c2p(-1.9, -45), RIGHT, buff=0)
        r2 = Text("2ª ordem (RLC)", font_size=20, color=COR_L).next_to(ax.c2p(-1.9, -58), RIGHT, buff=0)

        def degrau(H, x0, x1, cor, lado):
            y0, y1 = ganho_db(H, x0, db), ganho_db(H, x1, db)
            hor = DashedLine(ax.c2p(x0, y0), ax.c2p(x1, y0), color=cor, stroke_width=2)
            ver = Arrow(ax.c2p(x1, y0), ax.c2p(x1, y1), buff=0, color=cor, stroke_width=4,
                        max_tip_length_to_length_ratio=0.12)
            rot = Text(f"{y1 - y0:.0f} dB", font_size=22, color=cor).next_to(ver, lado, buff=0.12)
            return VGroup(hor, ver, rot)

        leg = self.legenda("Diagrama de Bode: ganho em dB × frequência em escala logarítmica")
        self.play(Create(ax), FadeIn(deco))
        self.play(Create(c1), FadeIn(r1), run_time=1.5)
        d1 = degrau(h1, 1, 2, COR_C, RIGHT)
        leg = self.legenda("1ª ordem: acima do corte, cai 20 dB a cada década (6 dB por oitava)", leg, COR_C)
        self.play(Create(d1))
        self.play(Create(c2), FadeIn(r2), run_time=1.5)
        d2 = degrau(h2, 1, 2, COR_L, LEFT)
        leg = self.legenda("2ª ordem: o dobro, 40 dB por década (12 dB por oitava)", leg, COR_L)
        self.play(Create(d2))
        self.play(Indicate(d2[2], color=COR_L))
        leg = self.legenda("Cada polo acrescenta −20 dB/década de inclinação", leg)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 3
    def cena_dinamica(self):
        self.titulo_cena("3 · Comportamento dinâmico")
        zeta = ValueTracker(2.0)
        sp = Axes(x_range=[-2.5, 1, 1], y_range=[-1.6, 1.6, 1], x_length=4.2, y_length=3.8,
                  axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO}).move_to(P(-4.4, -0.35))
        r_sp = VGroup(Text("Re", font_size=18, color=COR_EIXO).next_to(sp.x_axis.get_end(), DOWN, buff=0.1),
                      Text("Im", font_size=18, color=COR_EIXO).next_to(sp.y_axis.get_end(), LEFT, buff=0.1))
        cab_sp = Text("polos no plano s (ω₀ = 1)", font_size=20, color=GREY_A).next_to(sp, UP, buff=0.1)
        circ = DashedVMobject(Circle(radius=sp.c2p(1, 0)[0] - sp.c2p(0, 0)[0], color=GREY_D)
                              .move_to(sp.c2p(0, 0)), num_dashes=40)

        def polos():
            z = zeta.get_value()
            r = np.sqrt(complex(z * z - 1))
            return [-z + r, -z - r]

        def marcadores():
            return VGroup(*[Text("×", font_size=40, color=COR_L).move_to(sp.c2p(np.real(p), np.imag(p)))
                            for p in polos()])

        xs = always_redraw(marcadores)
        polo1 = Text("×", font_size=40, color=COR_C).move_to(sp.c2p(-1, 0)).shift(UP * 0.0)

        ax = eixos_tempo(P(2.8, -0.35), 6.6, 3.8, [0, 15, 5], [0, 1.8, 0.5])
        cab_ax = rotulo_eixo(ax, Text("resposta ao degrau", font_size=20, color=GREY_A))
        ref = DashedLine(ax.c2p(0, 1), ax.c2p(15, 1), color=GREY_D, stroke_width=2)
        c1 = ax.plot(lambda t: 1 - np.exp(-t), x_range=[0, 15, 0.02], color=COR_C, stroke_width=3)
        r1 = Text("1ª ordem: exponencial, sem overshoot", font_size=18, color=COR_C).next_to(
            ax.c2p(5.5, 0.55), RIGHT, buff=0)
        c2 = always_redraw(lambda: ax.plot(lambda t: degrau_2a(t, zeta.get_value()), x_range=[0, 15, 0.02],
                                           color=COR_L, stroke_width=4))

        def painel():
            z = zeta.get_value()
            ov = 100 * np.exp(-PI * z / np.sqrt(1 - z * z)) if z < 1 else 0.0
            return VGroup(
                Text(f"ζ = {z:.2f}    Q = 1/(2ζ) = {1 / (2 * z):.2f}", font_size=22, color=COR_L),
                Text(f"overshoot = {ov:.0f} %", font_size=22, color=COR_DESTAQUE if ov > 1 else GREY_A),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to(P(3.6, 2.35))

        info = always_redraw(painel)

        leg = self.legenda("1ª ordem: um único polo real, sem troca de energia entre armazenadores")
        self.play(Create(sp), FadeIn(r_sp), FadeIn(cab_sp), Create(circ))
        self.play(FadeIn(polo1))
        self.play(Create(ax), FadeIn(cab_ax), Create(ref))
        self.play(Create(c1), FadeIn(r1), run_time=1.5)
        leg = self.legenda("2ª ordem: dois polos; L e C trocam energia entre si", leg, COR_L)
        self.play(FadeOut(polo1))
        self.add(xs, c2)
        self.play(FadeIn(info))
        leg = self.legenda("ζ > 1: dois polos reais, resposta lenta e sem oscilação", leg)
        self.wait(1)
        leg = self.legenda("Diminuindo o amortecimento ζ, os polos se aproximam…", leg)
        self.play(zeta.animate.set_value(1.0), run_time=2.5)
        leg = self.legenda("…e viram um par complexo conjugado: aparecem ressonância e overshoot", leg,
                           COR_DESTAQUE)
        self.play(zeta.animate.set_value(0.5), run_time=2.5)
        self.play(zeta.animate.set_value(0.15), run_time=2.5)
        self.wait(0.8)
        leg = self.legenda("Q alto (ζ baixo) = ressonância forte e oscilação demorada", leg, COR_L)
        self.play(zeta.animate.set_value(0.707), run_time=2)
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 4
    def cena_primeira_ordem(self):
        self.titulo_cena("4 · Filtros de 1ª ordem")
        fio_rc, rc = self.malha(-5.9, -2.9, 0.7, 2.4, [("R", resistor, 0.2, 0.8)], capacitor, fonte)
        r_vin = tex(r"V_{in}", WHITE, 26).next_to(rc["esq"], LEFT, buff=0.12)
        r_r = tex("R", COR_R, 26).next_to(rc["R"], DOWN, buff=0.12)
        r_c = tex("C", COR_C, 26).next_to(rc["dir"], LEFT, buff=0.15)
        saida_lp = Text("V_C → passa-baixa", font_size=20, color=COR_LP).next_to(rc["dir"], RIGHT, buff=0.2)
        saida_hp = Text("V_R → passa-alta", font_size=20, color=COR_HP).next_to(rc["R"], UP, buff=0.18)

        f_lp = tex(r"H_{LP}(s) = \frac{K\,\omega_c}{s + \omega_c}", COR_LP, 32)
        f_hp = tex(r"H_{HP}(s) = \frac{K\,s}{s + \omega_c}", COR_HP, 32)
        f_wc = tex(r"\omega_c = \tfrac{1}{RC}\ \text{(RC)}\quad\text{ou}\quad \omega_c = \tfrac{R}{L}\ \text{(RL)}",
                   GREY_A, 26)
        formulas = VGroup(f_lp, f_hp, f_wc).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(P(2.6, 1.6))

        db = (-40, 10)
        ax, deco = eixos_bode(P(0.3, -1.55), 10.5, 2.4, db, passo=10, rotulo="ω/ωc")
        h_lp = lambda s: 1 / (s + 1)
        h_hp = lambda s: s / (s + 1)
        c_lp = curva_bode(ax, h_lp, COR_LP, db)
        c_hp = curva_bode(ax, h_hp, COR_HP, db)
        w = ValueTracker(-2.0)
        pts = always_redraw(lambda: VGroup(
            Dot(ax.c2p(w.get_value(), ganho_db(h_lp, w.get_value(), db)), radius=0.08, color=COR_LP),
            Dot(ax.c2p(w.get_value(), ganho_db(h_hp, w.get_value(), db)), radius=0.08, color=COR_HP),
            DashedLine(ax.c2p(w.get_value(), db[0]), ax.c2p(w.get_value(), db[1]), color=GREY_A, stroke_width=2)))
        leitura = always_redraw(lambda: Text(
            f"ω/ωc = {10 ** w.get_value():.2f}    |H_LP| = {abs(h_lp(1j * 10 ** w.get_value())):.2f}"
            f"    |H_HP| = {abs(h_hp(1j * 10 ** w.get_value())):.2f}", font_size=20, color=WHITE
        ).move_to(P(1.0, 0.0)))

        leg = self.legenda("Um único circuito RC série: a saída escolhida define o tipo de filtro")
        self.play(Create(fio_rc), *[Create(c) for c in rc.values()], FadeIn(r_vin), FadeIn(r_r), FadeIn(r_c),
                  run_time=1.5)
        self.play(FadeIn(saida_lp), Indicate(rc["dir"], color=COR_LP))
        self.play(Write(f_lp))
        self.play(FadeIn(saida_hp), Indicate(rc["R"], color=COR_HP))
        self.play(Write(f_hp))
        self.play(FadeIn(f_wc))
        leg = self.legenda("O numerador decide: sem s → passa-baixa; com s (zero na origem) → passa-alta", leg)
        self.play(Create(ax), FadeIn(deco))
        self.play(Create(c_lp), Create(c_hp), run_time=1.5)
        self.add(pts)
        self.play(FadeIn(leitura))
        leg = self.legenda("ω → 0: o capacitor fica aberto, V_C = V_in (LP passa) e V_R = 0 (HP bloqueia)", leg)
        self.wait(1)
        self.play(w.animate.set_value(0), run_time=2.5)
        leg = self.legenda("Em ω = ωc os dois valem 1/√2 (−3 dB): é a frequência de corte", leg, COR_DESTAQUE)
        self.wait(1)
        leg = self.legenda("ω → ∞: o capacitor vira curto, V_C → 0 (LP bloqueia) e V_R → V_in (HP passa)", leg)
        self.play(w.animate.set_value(2), run_time=2.5)
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 5
    def cena_segunda_ordem(self):
        self.titulo_cena("5 · Filtros de 2ª ordem: o mesmo denominador")
        d = tex(r"D(s) = s^2 + \frac{\omega_0}{Q}\,s + \omega_0^2 = s^2 + 2\zeta\omega_0\,s + \omega_0^2",
                WHITE, 32).move_to(P(0.6, 2.5))
        hs = VGroup(
            tex_partes([(r"H_{LP} = \frac{", WHITE), (r"K\omega_0^2", COR_LP), (r"}{D(s)}", WHITE)], 32),
            tex_partes([(r"H_{BP} = \frac{", WHITE), (r"K\frac{\omega_0}{Q}\,s", COR_BP), (r"}{D(s)}", WHITE)], 32),
            tex_partes([(r"H_{HP} = \frac{", WHITE), (r"K s^2", COR_HP), (r"}{D(s)}", WHITE)], 32),
        ).arrange(RIGHT, buff=1.0).move_to(P(0, 1.35))
        q = ValueTracker(0.707)
        db = (-60, 20)
        ax, deco = eixos_bode(P(0.3, -1.45), 11, 2.6, db)

        def H(tipo):
            def f(s):
                qq = q.get_value()
                den = s * s + s / qq + 1
                return {"lp": 1, "bp": s / qq, "hp": s * s}[tipo] / den
            return f

        curvas = always_redraw(lambda: VGroup(curva_bode(ax, H("lp"), COR_LP, db), curva_bode(ax, H("bp"), COR_BP, db),
                                              curva_bode(ax, H("hp"), COR_HP, db)))
        leitura = always_redraw(lambda: Text(f"Q = {q.get_value():.2f}   (ζ = {1 / (2 * q.get_value()):.2f})",
                                             font_size=22, color=COR_DESTAQUE).move_to(P(4.6, 0.35)))

        leg = self.legenda("Em 2ª ordem o denominador é sempre o mesmo: define ω₀ e o amortecimento")
        self.play(Write(d), run_time=1.5)
        leg = self.legenda("Só a potência de s no numerador (os zeros) muda o tipo de filtro", leg)
        self.play(LaggedStart(*[Write(h) for h in hs], lag_ratio=0.4), run_time=2.5)
        self.play(*[Indicate(h[1], scale_factor=1.25) for h in hs])
        self.play(Create(ax), FadeIn(deco))
        self.add(curvas)
        self.play(FadeIn(leitura))
        leg = self.legenda("LP: passa DC e cai 40 dB/déc · HP: o espelho · BP: pico em ω₀ e 20 dB/déc de cada lado",
                           leg)
        self.wait(1.5)
        leg = self.legenda("Q alto: pico de ressonância em ω₀ e banda passante estreita", leg, COR_DESTAQUE)
        self.play(q.animate.set_value(5), run_time=3)
        self.wait(0.8)
        leg = self.legenda("Q baixo: transição suave, sem pico", leg)
        self.play(q.animate.set_value(0.5), run_time=2.5)
        self.play(q.animate.set_value(0.707), run_time=1.5)
        self.wait(1)
        self.limpar()

    def cena_tabela_segunda(self):
        self.titulo_cena("5 · Resumo das formas de 2ª ordem")
        xs = [-5.0, -2.1, 0.7, 3.0, 5.3]
        cab = ["Tipo", "Numerador N(s)", "ω → 0", "ω = ω₀", "ω → ∞"]
        linhas = [
            (("Passa-baixa", COR_LP), r"K\omega_0^2", "K (máximo)", "depende de Q", "0"),
            (("Passa-banda", COR_BP), r"K\tfrac{\omega_0}{Q}\,s", "0", "K (pico)", "0"),
            (("Passa-alta", COR_HP), r"K s^2", "0", "depende de Q", "K (máximo)"),
        ]
        ys = [1.1, -0.2, -1.5]
        t_cab = VGroup(*[Text(c, font_size=22, color=GREY_A, weight=BOLD).move_to(P(x, 2.3)) for c, x in zip(cab, xs)])
        self.play(LaggedStart(*[FadeIn(t) for t in t_cab], lag_ratio=0.15))
        leg = self.legenda("Ganho nos três pontos-chave de cada forma")
        for (nome, num, a, b, c), y in zip(linhas, ys):
            cor = nome[1]
            sep = Line(P(-6.5, y + 0.62), P(6.5, y + 0.62), color=COR_EIXO, stroke_width=1.5)
            celulas = VGroup(Text(nome[0], font_size=22, color=cor, weight=BOLD).move_to(P(xs[0], y)),
                             tex(num, cor, 30).move_to(P(xs[1], y)),
                             *[Text(t, font_size=21, color=WHITE).move_to(P(x, y)) for t, x in zip((a, b, c), xs[2:])])
            self.play(Create(sep), FadeIn(celulas, shift=UP * 0.1), run_time=0.9)
            self.wait(0.8)
        leg = self.legenda("Ainda existe o rejeita-banda (notch), que aparece no RLC série a seguir", leg, COR_NOTCH)
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 6
    def cena_rlc_serie(self):
        self.titulo_cena("6 · Um RLC série, quatro filtros")
        R, Lv, Cv = 0.5, 1.0, 1.0
        fio_c, comp = self.malha(-5.9, -2.4, 0.75, 2.5,
                                 [("R", resistor, 0.12, 0.47), ("L", indutor, 0.53, 0.88)], capacitor, fonte)
        rot = VGroup(tex(r"V_{in}", WHITE, 26).next_to(comp["esq"], LEFT, buff=0.12),
                     tex("R", COR_R, 26).next_to(comp["R"], UP, buff=0.12),
                     tex("L", COR_L, 26).next_to(comp["L"], UP, buff=0.12),
                     tex("C", COR_C, 26).next_to(comp["dir"], RIGHT, buff=0.15))
        seta_i = Arrow(P(-5.9, 2.5) + RIGHT * 0.05, P(-5.4, 2.5), buff=0, color=COR_DESTAQUE, stroke_width=4,
                       max_tip_length_to_length_ratio=0.4)
        r_i = tex("I(s)", COR_DESTAQUE, 24).next_to(seta_i, DOWN, buff=0.08)

        der = VGroup(
            tex(r"Z_{total}(s) = R + sL + \frac{1}{sC}", WHITE, 28),
            tex(r"I(s) = \frac{s/L}{s^2 + \frac{R}{L}s + \frac{1}{LC}}\,V_{in}(s)", WHITE, 28),
            tex(r"\frac{V_{out}}{V_{in}} = Z_k(s)\cdot\frac{s/L}{s^2 + \frac{R}{L}s + \frac{1}{LC}}", COR_DESTAQUE, 28),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(P(2.9, 1.65))

        db = (-60, 20)
        ax, deco = eixos_bode(P(2.4, -1.55), 8.4, 2.0, db)
        den = lambda s: s * s + (R / Lv) * s + 1 / (Lv * Cv)
        casos = [
            ("dir", r"V_C:\ \frac{1/LC}{D(s)}", "passa-baixa", COR_LP, lambda s: (1 / (Lv * Cv)) / den(s)),
            ("L", r"V_L:\ \frac{s^2}{D(s)}", "passa-alta", COR_HP, lambda s: s * s / den(s)),
            ("R", r"V_R:\ \frac{\frac{R}{L}s}{D(s)}", "passa-banda", COR_BP, lambda s: (R / Lv) * s / den(s)),
            ("LC", r"V_{LC}:\ \frac{s^2 + \frac{1}{LC}}{D(s)}", "rejeita-banda", COR_NOTCH,
             lambda s: (s * s + 1 / (Lv * Cv)) / den(s)),
        ]
        explicacoes = [
            "Sobre o capacitor: o s se cancela, sobra uma constante ⇒ passa-baixa",
            "Sobre o indutor: sobra s² no numerador ⇒ passa-alta",
            "Sobre o resistor: sobra s¹ ⇒ passa-banda, máximo em ω₀ = 1/√(LC)",
            "Sobre L e C juntos: o numerador zera em ω₀ ⇒ rejeita-banda (notch)",
        ]

        leg = self.legenda("A mesma corrente I(s) atravessa R, L e C")
        self.play(Create(fio_c), *[Create(c) for c in comp.values()], FadeIn(rot), run_time=1.5)
        self.play(GrowArrow(seta_i), FadeIn(r_i))
        leg = self.legenda("Impedância total, corrente e tensão em cada componente", leg)
        for linha in der:
            self.play(Write(linha), run_time=1.2)
        self.play(Create(ax), FadeIn(deco))

        lista = VGroup()
        for k, ((nome, f, tipo, cor, H), expl) in enumerate(zip(casos, explicacoes)):
            alvo = VGroup(comp["L"], comp["dir"]) if nome == "LC" else comp[nome]
            caixa = SurroundingRectangle(alvo, color=cor, buff=0.12)
            linha = VGroup(tex(f, cor, 26), Text("→ " + tipo, font_size=18, color=cor)).arrange(RIGHT, buff=0.2)
            linha.move_to(P(-4.4, 0.05 - 0.78 * k)).align_to(P(-6.6, 0), LEFT)
            curva = curva_bode(ax, H, cor, db)
            leg = self.legenda(expl, leg, cor)
            self.play(Create(caixa))
            self.play(Write(linha), Create(curva), run_time=1.6)
            self.wait(0.6)
            self.play(FadeOut(caixa))
            lista.add(linha)
        leg = self.legenda("Mesmo circuito: só muda onde se mede a saída", leg, COR_DESTAQUE)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 7
    def cena_serie_paralelo(self):
        self.titulo_cena("7 · RLC série × RLC paralelo")
        w = ValueTracker(0.25)

        # ---- série (fonte de tensão)
        Rs = 0.25
        fio_s, cs = self.malha(-6.3, -3.3, 0.65, 2.3,
                               [("R", resistor, 0.1, 0.48), ("L", indutor, 0.52, 0.9)], capacitor, fonte)
        cab_s = Text("Série (fonte de tensão)", font_size=22, color=COR_LP, weight=BOLD).move_to(P(-4.8, 2.72))

        def zs(x):
            return Rs + 1j * (x - 1 / x)

        ax_s = eixos_tempo(P(-3.6, -1.4), 6.0, 2.3, [0, 3, 1], [0, 8, 2])
        r_axs = rotulo_eixo(ax_s, Text("|Z| / R", font_size=18, color=COR_LP))
        c_s = ax_s.plot(lambda x: min(abs(zs(x)) / Rs, 8), x_range=[0.12, 3, 0.005], color=COR_LP, stroke_width=4)
        m_s = Text("ω/ω₀", font_size=16, color=COR_EIXO).next_to(ax_s, DOWN, buff=0.05).align_to(ax_s, RIGHT)

        def barra(x, y, frac, cor, rotulo):
            base = Rectangle(width=0.35, height=1.6, color=COR_EIXO, stroke_width=1.5).move_to(P(x, y))
            ench = Rectangle(width=0.35, height=max(1.6 * frac, 0.01), stroke_width=0, fill_color=cor,
                             fill_opacity=0.85).move_to(base.get_bottom(), aligned_edge=DOWN)
            return VGroup(base, ench, Text(rotulo, font_size=16, color=cor).next_to(base, DOWN, buff=0.08))

        barra_s = always_redraw(lambda: barra(-2.5, 1.45, min(Rs / abs(zs(w.get_value())), 1), COR_LP, "|I|"))

        # ---- paralelo (fonte de corrente)
        Rp, Lp, Cp = 1.0, 0.25, 4.0
        xs = [0.8, 2.0, 3.1, 4.2]
        yt, yb = 2.3, 0.65
        fios_p = VGroup(fio([P(xs[0], yt), P(xs[-1], yt)]), fio([P(xs[0], yb), P(xs[-1], yb)]))
        cp = {"I": fonte(P(xs[0], yb), P(xs[0], yt)), "R": resistor(P(xs[1], yt), P(xs[1], yb)),
              "L": indutor(P(xs[2], yt), P(xs[2], yb)), "C": capacitor(P(xs[3], yt), P(xs[3], yb))}
        cab_p = Text("Paralelo (fonte de corrente)", font_size=22, color=COR_BP, weight=BOLD).move_to(P(2.5, 2.72))

        def zp(x):
            return 1 / (1 / Rp + 1j * (x * Cp - 1 / (x * Lp)))

        ax_p = eixos_tempo(P(3.6, -1.4), 6.0, 2.3, [0, 3, 1], [0, 1.1, 0.5])
        r_axp = rotulo_eixo(ax_p, Text("|Z| / R", font_size=18, color=COR_BP))
        c_p = ax_p.plot(lambda x: abs(zp(x)) / Rp, x_range=[0.05, 3, 0.005], color=COR_BP, stroke_width=4)
        m_p = Text("ω/ω₀", font_size=16, color=COR_EIXO).next_to(ax_p, DOWN, buff=0.05).align_to(ax_p, RIGHT)
        barras_p = always_redraw(lambda: VGroup(
            barra(5.2, 1.45, abs(zp(w.get_value()) / Rp), COR_R, "i_R"),
            barra(6.0, 1.45, abs(1 - zp(w.get_value()) / Rp), COR_L, "i_LC")))

        cursores = always_redraw(lambda: VGroup(
            Dot(ax_s.c2p(w.get_value(), min(abs(zs(w.get_value())) / Rs, 8)), radius=0.08, color=WHITE),
            Dot(ax_p.c2p(w.get_value(), abs(zp(w.get_value())) / Rp), radius=0.08, color=WHITE)))

        leg = self.legenda("Mesmos componentes, ligados de dois jeitos diferentes")
        self.play(FadeIn(cab_s), Create(fio_s), *[Create(c) for c in cs.values()], run_time=1.3)
        self.play(FadeIn(cab_p), Create(fios_p), *[Create(c) for c in cp.values()], run_time=1.3)
        self.play(Create(ax_s), FadeIn(r_axs), FadeIn(m_s), Create(ax_p), FadeIn(r_axp), FadeIn(m_p))
        self.play(Create(c_s), Create(c_p), run_time=1.5)
        self.add(cursores, barra_s, barras_p)
        leg = self.legenda("Baixa frequência: no série o C bloqueia; no paralelo o L desvia a corrente", leg)
        self.wait(1)
        leg = self.legenda("Na ressonância as reatâncias se anulam", leg, COR_DESTAQUE)
        self.play(w.animate.set_value(1.0), run_time=3.5)
        n_s = Text("L–C em curto: |Z| mínima = R\n⇒ corrente máxima", font_size=18, color=COR_LP
                   ).next_to(ax_s.c2p(1, 1), UR, buff=0.15)
        n_p = Text("L∥C aberto: |Z| máxima = R\n⇒ toda a corrente passa por R", font_size=18, color=COR_BP
                   ).next_to(ax_p.c2p(1.2, 0.7), RIGHT, buff=0.1)
        self.play(FadeIn(n_s), FadeIn(n_p))
        leg = self.legenda("Série: mínimo de impedância · Paralelo: máximo de impedância", leg, COR_DESTAQUE)
        self.wait(1.5)
        leg = self.legenda("Alta frequência: no série o L bloqueia; no paralelo o C desvia a corrente", leg)
        self.play(w.animate.set_value(2.8), run_time=3)
        self.wait(1)
        leg = self.legenda("Nos dois casos o pico passa-banda ocorre em ω₀ (dualidade corrente ↔ tensão)", leg)
        self.play(w.animate.set_value(1.0), run_time=2)
        self.wait(1.5)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo")
        itens = VGroup(*[Text(t, font_size=23, color=c) for t, c in [
            ("• Ordem = grau de D(s) = nº de polos = nº de elementos reativos", WHITE),
            ("• Cada polo: −20 dB/década; 2ª ordem: −40 dB/década", GREY_A),
            ("• 2ª ordem pode ressoar: ζ baixo (Q alto) ⇒ pico e overshoot", COR_L),
            ("• 1ª ordem: LP (Kωc/(s+ωc)) e HP (Ks/(s+ωc))", COR_C),
            ("• 2ª ordem: mesmo D(s); numerador s⁰, s¹, s² ⇒ LP, BP, HP", COR_BP),
            ("• RLC série: V_C, V_L, V_R, V_LC ⇒ LP, HP, BP, notch", COR_HP),
            ("• Série: |Z| mínima em ω₀ · Paralelo: |Z| máxima em ω₀", COR_LP),
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(P(0, -0.2))
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in itens], lag_ratio=0.3), run_time=4)
        self.wait(3)
        self.limpar()
