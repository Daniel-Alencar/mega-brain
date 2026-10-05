# -*- coding: utf-8 -*-
"""
Modelagem de uma cavidade de RF: do campo 3D ao filtro passa-banda
==================================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/Modelagem de uma cavidade de RF/modelagem_cavidade.py" ModelagemCavidade   # rascunho
    manim -pqh "src/Modelagem de uma cavidade de RF/modelagem_cavidade.py" ModelagemCavidade   # final

Requer LaTeX (MathTex).

Roteiro (segue "docs/Modelagem de uma cavidade de RF"):
    Abertura
    Cena 1 - Por que RLC paralelo: campo E ↔ C, campo B ↔ L, perdas nas paredes ↔ R
    Cena 2 - O circuito equivalente: gerador (Norton), acoplador 1:n, cavidade e feixe
    Cena 3 - Rebatendo Z0 pelo transformador: Z0' = n²·Z0
    Cena 4 - Lei dos nós e a equação diferencial de 2ª ordem
    Cena 5 - Transformada de Laplace: a impedância V_C(s)/I_C(s)
    Cena 6 - Comparação com a forma canônica do passa-banda de 2ª ordem
    Cena 7 - Resposta em frequência: L em curto, C em curto e L∥C aberto em ω0
    Resumo

Convenção: i_C(t) = i_rf(t) + i_b(t) é a corrente de excitação total;
a corrente no capacitor é chamada i_cap.
"""

import numpy as np
from manim import *

# Paleta didática (fixa em todas as cenas)
COR_C = GOLD             # capacitor / campo elétrico
COR_L = TEAL             # indutor / campo magnético
COR_R = GREY_A           # resistor / perdas
COR_RF = BLUE            # gerador de RF
COR_FEIXE = PINK         # feixe de elétrons
COR_ACOPLA = PURPLE_B    # acoplador / transformador
COR_DESTAQUE = YELLOW
COR_ERRO = RED
COBRE = "#c87533"
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}
Q_CARREGADO = 5.0        # fator de qualidade usado no gráfico de |Z(jω)|


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


def fonte(a, b, cor=WHITE, largura=4, raio=0.3):
    """Fonte senoidal de corrente (círculo com ~) entre a e b."""
    L = np.linalg.norm(b - a)
    g = _colocar(VGroup(Line(P(0, 0), P(L / 2 - raio, 0)), Circle(radius=raio).move_to(P(L / 2, 0)),
                        Line(P(L / 2 + raio, 0), P(L, 0))).set_stroke(cor, largura), a, b)
    seno = ParametricFunction(lambda t: P(t, 0.09 * np.sin(PI * t / 0.16)), t_range=[-0.16, 0.16],
                              color=cor, stroke_width=3).move_to((a + b) / 2)
    return VGroup(g, seno)


def circuito_original(yt, yb, compacto=False):
    """Circuito da cavidade com o transformador (gerador de Norton no primário)."""
    if compacto:
        x = dict(src=-6.3, z0=-5.3, p=-4.35, s=-3.75, R=-2.65, L=-1.45, C=-0.25, Ib=0.95)
    else:
        x = dict(src=-6.2, z0=-5.0, p=-3.9, s=-3.2, R=-1.9, L=-0.3, C=1.3, Ib=2.9)
    c = {
        "src": fonte(P(x["src"], yb), P(x["src"], yt), COR_RF),
        "Z0": resistor(P(x["z0"], yt), P(x["z0"], yb), COR_RF),
        "prim": indutor(P(x["p"], yt), P(x["p"], yb), COR_ACOPLA, voltas=5, r=0.1),
        "sec": indutor(P(x["s"], yb), P(x["s"], yt), COR_ACOPLA, voltas=5, r=0.1),
        "R": resistor(P(x["R"], yt), P(x["R"], yb)),
        "L": indutor(P(x["L"], yt), P(x["L"], yb)),
        "C": capacitor(P(x["C"], yt), P(x["C"], yb)),
        "Ib": fonte(P(x["Ib"], yb), P(x["Ib"], yt), COR_FEIXE),
    }
    fios = {
        "prim": VGroup(fio([P(x["src"], yt), P(x["p"], yt)]), fio([P(x["src"], yb), P(x["p"], yb)])),
        "sec": VGroup(fio([P(x["s"], yt), P(x["Ib"], yt)]), fio([P(x["s"], yb), P(x["Ib"], yb)])),
    }
    rot = {
        "src": tex(r"I'_{rf}", COR_RF, 28).next_to(c["src"], LEFT, buff=0.12),
        "Z0": tex(r"Z_0", COR_RF, 28).next_to(c["Z0"], RIGHT, buff=0.15),
        "n": tex(r"1:n", COR_ACOPLA, 28).move_to(P((x["p"] + x["s"]) / 2, yb - 0.35)),
        "R": tex("R", COR_R, 28).next_to(c["R"], LEFT, buff=0.15),
        "L": tex("L", COR_L, 28).next_to(c["L"], LEFT, buff=0.15),
        "C": tex("C", COR_C, 28).next_to(c["C"], LEFT, buff=0.15),
        "Ib": tex(r"I_b", COR_FEIXE, 28).next_to(c["Ib"], RIGHT, buff=0.12),
    }
    return c, fios, rot, x


def circuito_rebatido(yt, yb):
    """Tudo no secundário: I_rf, n²Z0, R, L, C e I_b em paralelo."""
    x = dict(src=-5.6, z=-4.0, R=-2.4, L=-0.8, C=0.8, Ib=2.4)
    c = {
        "src": fonte(P(x["src"], yb), P(x["src"], yt), COR_RF),
        "Z": resistor(P(x["z"], yt), P(x["z"], yb), COR_RF),
        "R": resistor(P(x["R"], yt), P(x["R"], yb)),
        "L": indutor(P(x["L"], yt), P(x["L"], yb)),
        "C": capacitor(P(x["C"], yt), P(x["C"], yb)),
        "Ib": fonte(P(x["Ib"], yb), P(x["Ib"], yt), COR_FEIXE),
    }
    fios = VGroup(fio([P(x["src"], yt), P(x["Ib"], yt)]), fio([P(x["src"], yb), P(x["Ib"], yb)]))
    rot = {
        "src": tex(r"I_{rf}", COR_RF, 28).next_to(c["src"], LEFT, buff=0.12),
        "Z": tex(r"n^2 Z_0", COR_RF, 28).next_to(c["Z"], LEFT, buff=0.15),
        "R": tex("R", COR_R, 28).next_to(c["R"], LEFT, buff=0.15),
        "L": tex("L", COR_L, 28).next_to(c["L"], LEFT, buff=0.15),
        "C": tex("C", COR_C, 28).next_to(c["C"], LEFT, buff=0.15),
        "Ib": tex(r"I_b", COR_FEIXE, 28).next_to(c["Ib"], RIGHT, buff=0.12),
    }
    return c, fios, rot, x


def impedancia_norm(w):
    """Z(jω)/(R ∥ n²Z0) com ω normalizado por ω0."""
    w = max(w, 1e-4)
    return 1 / (1 + 1j * Q_CARREGADO * (w - 1 / w))


# =============================================================================
# Cena
# =============================================================================
class ModelagemCavidade(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_cavidade()
        self.cena_circuito()
        self.cena_rebater()
        self.cena_kcl()
        self.cena_laplace()
        self.cena_canonica()
        self.cena_frequencia()
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
        titulo = Text("Modelagem de uma cavidade de RF", font_size=52, weight=BOLD)
        sub = Text("Do campo eletromagnético 3D a um filtro passa-banda de 2ª ordem", font_size=28, color=GREY_A)
        mapa = tex(r"\text{cavidade} \;\longrightarrow\; RLC\ \text{paralelo}", COR_DESTAQUE, 36)
        g = VGroup(titulo, sub, mapa).arrange(DOWN, buff=0.4)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(mapa, shift=UP * 0.2))
        self.wait(1.2)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_cavidade(self):
        self.titulo_cena("1 · Por que um RLC paralelo?")
        cx, cy, W, H = -3.7, -0.3, 3.4, 3.0
        paredes = VGroup(
            fio([P(cx - W / 2, cy + 0.3), P(cx - W / 2, cy + H / 2), P(cx + W / 2, cy + H / 2), P(cx + W / 2, cy + 0.3)]),
            fio([P(cx - W / 2, cy - 0.3), P(cx - W / 2, cy - H / 2), P(cx + W / 2, cy - H / 2), P(cx + W / 2, cy - 0.3)]),
            fio([P(cx - W / 2 - 0.9, cy + 0.3), P(cx - W / 2, cy + 0.3)]),
            fio([P(cx - W / 2 - 0.9, cy - 0.3), P(cx - W / 2, cy - 0.3)]),
            fio([P(cx + W / 2, cy + 0.3), P(cx + W / 2 + 0.9, cy + 0.3)]),
            fio([P(cx + W / 2, cy - 0.3), P(cx + W / 2 + 0.9, cy - 0.3)]),
        ).set_stroke(COBRE, 7)
        eixo = DashedLine(P(cx - W / 2 - 0.9, cy), P(cx + W / 2 + 0.9, cy), color=GREY_B, stroke_width=2)
        r_eixo = Text("eixo do feixe", font_size=16, color=GREY_B).next_to(P(cx + W / 2 + 0.9, cy), DOWN, buff=0.35
                                                                          ).shift(LEFT * 0.4)
        r_cav = Text("cavidade de cobre (corte lateral), modo TM₀₁₀", font_size=18, color=COBRE
                     ).next_to(paredes, UP, buff=0.15)
        t = ValueTracker(0.0)

        def campo_e():
            amp = np.cos(TAU * t.get_value())
            g = VGroup()
            for r in (0, 0.45, -0.45, 0.9, -0.9):
                comp = 2.6 * np.cos(PI / 2 * r / 1.35) * amp
                if abs(comp) < 0.08:
                    continue
                g.add(Arrow(P(cx - comp / 2, cy + r), P(cx + comp / 2, cy + r), buff=0, color=COR_C,
                            stroke_width=4, max_tip_length_to_length_ratio=0.15))
            return g

        def campo_b():
            b = np.sin(TAU * t.get_value())
            g = VGroup()
            raio = 0.04 + 0.16 * abs(b)
            for y, sinal in ((cy + 1.1, 1), (cy - 1.1, -1)):
                fora = b * sinal > 0
                for x in (cx - 1.0, cx, cx + 1.0):
                    c = Circle(radius=raio, color=COR_L, stroke_width=3).move_to(P(x, y))
                    if fora:
                        g.add(VGroup(c, Dot(P(x, y), radius=raio * 0.35, color=COR_L)))
                    else:
                        d = raio * 0.6
                        g.add(VGroup(c, Line(P(x - d, y - d), P(x + d, y + d)), Line(P(x - d, y + d), P(x + d, y - d))
                                     ).set_stroke(COR_L, 3))
            return g

        e_mob = always_redraw(campo_e)
        b_mob = always_redraw(campo_b)
        base = -1.7

        def barras():
            th = TAU * t.get_value()
            g = VGroup()
            for x, val, cor, nome in ((0.6, np.cos(th) ** 2, COR_C, r"W_E"), (1.6, np.sin(th) ** 2, COR_L, r"W_M")):
                moldura = Rectangle(width=0.55, height=2.8, color=COR_EIXO, stroke_width=1.5).move_to(P(x, base + 1.4))
                ench = Rectangle(width=0.55, height=max(2.8 * val, 0.01), stroke_width=0, fill_color=cor,
                                 fill_opacity=0.85).move_to(P(x, base), aligned_edge=DOWN)
                g.add(moldura, ench, tex(nome, cor, 28).next_to(moldura, DOWN, buff=0.1))
            return g

        energia = always_redraw(barras)
        r_energia = Text("energia armazenada", font_size=18, color=GREY_A).move_to(P(1.1, base + 3.1))

        # Circuito equivalente (direita)
        yt, yb = 1.0, -1.0
        xr, xl, xc = 3.4, 4.7, 6.0
        trilhos = VGroup(fio([P(xr, yt), P(xc, yt)]), fio([P(xr, yb), P(xc, yb)]))
        comp_r = resistor(P(xr, yt), P(xr, yb))
        comp_l = indutor(P(xl, yt), P(xl, yb))
        comp_c = capacitor(P(xc, yt), P(xc, yb))
        r_r = tex("R", COR_R, 28).next_to(comp_r, LEFT, buff=0.15)
        r_l = tex("L", COR_L, 28).next_to(comp_l, LEFT, buff=0.15)
        r_c = tex("C", COR_C, 28).next_to(comp_c, LEFT, buff=0.15)
        notas = VGroup(
            tex_partes([(r"C:\ ", COR_C), (r"W_E = \tfrac{1}{2} C V_c^2", WHITE)], 26),
            tex_partes([(r"L:\ ", COR_L), (r"W_M = \tfrac{1}{2} L I_L^2", WHITE)], 26),
            VGroup(tex(r"R:", COR_R, 26), Text("perdas Joule (resistência shunt)", font_size=18, color=WHITE)
                   ).arrange(RIGHT, buff=0.15),
            tex(r"\omega_0 = \frac{1}{\sqrt{LC}}", COR_DESTAQUE, 28),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(P(4.6, -2.15))

        leg = self.legenda("Uma cavidade de RF é um volume oco de cobre onde a onda fica confinada")
        self.play(Create(paredes), Create(eixo), FadeIn(r_eixo), FadeIn(r_cav), run_time=1.5)
        self.add(e_mob, b_mob)
        leg = self.legenda("Campo elétrico axial (dourado) e campo magnético azimutal (⊙ / ⊗)", leg)
        self.play(t.animate.set_value(1), run_time=4, rate_func=linear)
        self.play(FadeIn(r_energia))
        self.add(energia)
        leg = self.legenda("A energia passa do campo elétrico para o magnético e volta, a cada meio ciclo", leg)
        self.play(t.animate.set_value(2.5), run_time=6, rate_func=linear)

        leg = self.legenda("Campo E concentrado no eixo ⇒ comporta-se como um capacitor", leg, COR_C)
        self.play(Create(trilhos))
        self.play(TransformFromCopy(campo_e(), comp_c), FadeIn(r_c), run_time=1.5)
        self.play(FadeIn(notas[0]))
        leg = self.legenda("Campo B circulando perto das paredes ⇒ comporta-se como um indutor", leg, COR_L)
        self.play(t.animate.set_value(2.75), run_time=0.8)
        self.play(TransformFromCopy(campo_b(), comp_l), FadeIn(r_l), run_time=1.5)
        self.play(FadeIn(notas[1]))
        leg = self.legenda("Correntes nas paredes de cobre (condutividade finita) dissipam calor ⇒ R", leg, COR_R)
        self.play(paredes.animate.set_stroke(ORANGE, 9), run_time=0.8)
        self.play(TransformFromCopy(paredes, comp_r), FadeIn(r_r), paredes.animate.set_stroke(COBRE, 7), run_time=1.5)
        self.play(FadeIn(notas[2]))
        leg = self.legenda("Na ressonância: impedância máxima e puramente resistiva", leg, COR_DESTAQUE)
        self.play(Write(notas[3]))
        self.play(t.animate.set_value(3.5), run_time=3, rate_func=linear)
        self.wait(0.8)
        self.limpar()

    # ================================================================== CENA 2
    def cena_circuito(self):
        self.titulo_cena("2 · O circuito equivalente completo")
        yt, yb = 1.2, -1.0
        c, fios, rot, x = circuito_original(yt, yb, compacto=True)
        cabecalhos = VGroup(
            Text("Gerador de RF", font_size=20, color=COR_RF).move_to(P((x["src"] + x["z0"]) / 2, yt + 0.45)),
            Text("Acoplador", font_size=20, color=COR_ACOPLA).move_to(P((x["p"] + x["s"]) / 2, yt + 0.45)),
            Text("Cavidade", font_size=20, color=COR_DESTAQUE).move_to(P((x["R"] + x["C"]) / 2, yt + 0.45)),
            Text("Feixe", font_size=20, color=COR_FEIXE).move_to(P(x["Ib"], yt + 0.45)),
        )
        mapas = VGroup(
            Text("Amplificador + linha → fonte I′rf ∥ Z₀ (Norton)", font_size=18, color=COR_RF),
            Text("Antena / espira → transformador 1:n", font_size=18, color=COR_ACOPLA),
            Text("Cavidade metálica → RLC paralelo", font_size=18, color=COR_DESTAQUE),
            Text("Feixe relativístico → fonte de corrente I_b", font_size=18, color=COR_FEIXE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(P(4.2, 0.1)).align_to(P(2.0, 0), LEFT)
        beta = tex(r"\beta = \frac{R}{n^2 Z_0}", COR_ACOPLA, 30).move_to(P(-4.05, -2.0))
        r_beta = Text("fator de acoplamento", font_size=18, color=COR_ACOPLA).next_to(beta, DOWN, buff=0.08)

        leg = self.legenda("A cavidade vira um RLC paralelo")
        self.play(Create(fios["sec"]), *[Create(c[k]) for k in ("R", "L", "C")],
                  *[FadeIn(rot[k]) for k in ("R", "L", "C")], FadeIn(cabecalhos[2]), run_time=1.5)
        self.play(FadeIn(mapas[2], shift=LEFT * 0.2))

        leg = self.legenda("O amplificador e a linha (Z₀ ≈ 50 Ω) viram uma fonte de corrente com Z₀ em paralelo", leg,
                           COR_RF)
        self.play(Create(fios["prim"]), Create(c["src"]), Create(c["Z0"]), FadeIn(rot["src"]), FadeIn(rot["Z0"]),
                  FadeIn(cabecalhos[0]), run_time=1.5)
        self.play(FadeIn(mapas[0], shift=LEFT * 0.2))

        leg = self.legenda("A cavidade tem megaohms; a linha, 50 Ω: o acoplador adapta as impedâncias", leg, COR_ACOPLA)
        self.play(Create(c["prim"]), Create(c["sec"]), FadeIn(rot["n"]), FadeIn(cabecalhos[1]), run_time=1.5)
        self.play(FadeIn(mapas[1], shift=LEFT * 0.2))
        self.play(Write(beta), FadeIn(r_beta))

        # O feixe: pacotes periódicos a v ≈ c
        leg = self.legenda("O feixe passa em pacotes curtos e periódicos, quase à velocidade da luz", leg, COR_FEIXE)
        self.play(Create(c["Ib"]), FadeIn(rot["Ib"]), FadeIn(cabecalhos[3]))
        trilha = Line(P(-2.6, -2.1), P(2.5, -2.1), color=GREY_D, stroke_width=2)
        desloc = ValueTracker(0.0)
        pacotes = always_redraw(lambda: VGroup(*[
            Ellipse(width=0.32, height=0.16, color=COR_FEIXE, fill_opacity=0.9).move_to(
                P(-2.6 + ((k * 0.85 + desloc.get_value()) % 5.1), -2.1)) for k in range(6)]))
        r_pac = Text("v ≈ c: a corrente não depende da tensão da cavidade", font_size=18, color=COR_FEIXE
                     ).next_to(trilha, DOWN, buff=0.15)
        self.play(Create(trilha), FadeIn(r_pac))
        self.add(pacotes)
        self.play(desloc.animate.set_value(5.1), run_time=4, rate_func=linear)
        self.play(FadeIn(mapas[3], shift=LEFT * 0.2))
        leg = self.legenda("Fonte de corrente quase ideal, que induz campos contrários (beam loading)", leg, COR_FEIXE)
        self.play(desloc.animate.set_value(10.2), run_time=4, rate_func=linear)
        leg = self.legenda("Maxwell 3D ⇒ circuito linear simples, perto da ressonância de interesse", leg, COR_DESTAQUE)
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 3
    def cena_rebater(self):
        self.titulo_cena("3 · Rebatendo a impedância pelo transformador")
        yt, yb = 2.3, 0.6
        c, fios, rot, x = circuito_original(yt, yb)
        todos = VGroup(*c.values(), *fios.values(), *rot.values())
        self.play(FadeIn(todos))
        trafo = VGroup(c["prim"], c["sec"], rot["n"])
        caixa = SurroundingRectangle(trafo, color=COR_ACOPLA, buff=0.15)
        eqs = VGroup(
            tex(r"V_2 = n\,V_1", WHITE, 32),
            tex(r"I_2 = \frac{I_1}{n}", WHITE, 32),
            tex(r"Z_0' = \frac{V_2}{I_2} = \frac{n V_1}{I_1 / n} = n^2\frac{V_1}{I_1} = n^2 Z_0", COR_DESTAQUE, 32),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(P(-1.6, -1.35))

        leg = self.legenda("Transformador ideal 1:n: a tensão sobe n vezes e a corrente cai n vezes")
        self.play(Create(caixa))
        self.play(Write(eqs[0]))
        self.play(Write(eqs[1]))
        leg = self.legenda("Vista do secundário, a impedância da linha é multiplicada por n²", leg, COR_DESTAQUE)
        self.play(Write(eqs[2]), run_time=2)
        self.play(Indicate(eqs[2], color=COR_DESTAQUE))

        c2, fios2, rot2, _ = circuito_rebatido(yt, yb)
        leg = self.legenda("Eliminamos o transformador: tudo passa para o lado da cavidade", leg)
        self.play(FadeOut(caixa))
        self.play(
            FadeOut(VGroup(c["prim"], c["sec"], rot["n"])),
            ReplacementTransform(VGroup(fios["prim"], fios["sec"]), fios2),
            ReplacementTransform(c["src"], c2["src"]), ReplacementTransform(c["Z0"], c2["Z"]),
            ReplacementTransform(rot["src"], rot2["src"]), ReplacementTransform(rot["Z0"], rot2["Z"]),
            *[ReplacementTransform(c[k], c2[k]) for k in ("R", "L", "C", "Ib")],
            *[ReplacementTransform(rot[k], rot2[k]) for k in ("R", "L", "C", "Ib")],
            run_time=2.5)
        leg = self.legenda("A fonte vista no secundário passa a se chamar I_rf; a linha vira n²·Z₀", leg, COR_RF)
        self.play(Indicate(rot2["Z"], color=COR_DESTAQUE), Indicate(rot2["src"], color=COR_DESTAQUE))
        r_par = Text("seis ramos em paralelo, todos sob a mesma tensão v_C(t)", font_size=22, color=COR_DESTAQUE
                     ).move_to(P(-1.6, 0.05))
        self.play(FadeIn(r_par))
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 4
    def cena_kcl(self):
        self.titulo_cena("4 · Lei dos nós e a equação diferencial")
        yt, yb = 2.3, 0.7
        c, fios, rot, x = circuito_rebatido(yt, yb)
        self.play(FadeIn(VGroup(*c.values(), fios)))
        no = Dot(P(x["L"] + 0.8, yt), radius=0.09, color=COR_DESTAQUE)
        r_no = tex(r"v_C(t)", COR_DESTAQUE, 28).next_to(no, UP, buff=0.1)
        ym = (yt + yb) / 2

        def seta_ramo(xx, para_cima, cor, nome):
            a, b = P(xx + 0.38, ym - 0.3), P(xx + 0.38, ym + 0.3)
            if not para_cima:
                a, b = b, a
            s = Arrow(a, b, buff=0, color=cor, stroke_width=4, max_tip_length_to_length_ratio=0.3)
            return VGroup(s, tex(nome, cor, 22).next_to(s, RIGHT, buff=0.06))

        entradas = VGroup(seta_ramo(x["src"], True, COR_RF, r"i_{rf}"), seta_ramo(x["Ib"], True, COR_FEIXE, r"i_b"))
        saidas = VGroup(seta_ramo(x["z"], False, COR_RF, r"i_Z"), seta_ramo(x["R"], False, COR_R, r"i_R"),
                        seta_ramo(x["L"], False, COR_L, r"i_L"), seta_ramo(x["C"], False, COR_C, r"i_{cap}"))

        ramos = VGroup(
            tex(r"i_Z = \frac{v_C}{n^2 Z_0}", COR_RF, 26),
            tex(r"i_R = \frac{v_C}{R}", COR_R, 26),
            tex(r"i_L = \frac{1}{L}\int v_C\,dt", COR_L, 26),
            tex(r"i_{cap} = C\,\frac{dv_C}{dt}", COR_C, 26),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(P(5.1, 1.35))

        k1 = tex_partes([(r"i_C(t) = ", WHITE), (r"i_{rf}(t)", COR_RF), (r" + ", WHITE), (r"i_b(t)", COR_FEIXE)], 32
                        ).move_to(P(-3.0, -0.15))
        r_k1 = Text("corrente de excitação que entra no nó", font_size=18, color=GREY_A).next_to(k1, RIGHT, buff=0.3)
        passos = [
            r"i_C = \frac{v_C}{n^2 Z_0} + \frac{v_C}{R} + \frac{1}{L}\int v_C\,dt + C\frac{dv_C}{dt}",
            r"C\frac{dv_C}{dt} + \left(\frac{R + n^2 Z_0}{n^2 R Z_0}\right) v_C + \frac{1}{L}\int v_C\,dt = i_C",
            r"C\frac{d^2 v_C}{dt^2} + \left(\frac{R + n^2 Z_0}{n^2 R Z_0}\right)\frac{dv_C}{dt} + \frac{v_C}{L} = \frac{di_C}{dt}",
            r"\ddot{v}_C + \frac{n^2 Z_0 + R}{n^2 R Z_0 C}\,\dot{v}_C + \frac{1}{LC}\,v_C = \frac{1}{C}\,\dot{i}_C",
        ]
        explicacoes = [
            "Lei dos nós: o que entra é igual à soma do que sai pelos quatro ramos passivos",
            "Juntando os dois termos resistivos",
            "Derivando no tempo para eliminar a integral do indutor",
            "Dividindo por C: equação diferencial de 2ª ordem da cavidade",
        ]

        leg = self.legenda("Todos os ramos estão em paralelo, sob a mesma tensão v_C(t)")
        self.play(GrowFromCenter(no), FadeIn(r_no))
        leg = self.legenda("Gerador e feixe injetam corrente no nó", leg, COR_RF)
        self.play(*[GrowArrow(e[0]) for e in entradas], *[FadeIn(e[1]) for e in entradas])
        self.play(Write(k1), FadeIn(r_k1))
        leg = self.legenda("A corrente se divide pelos ramos passivos", leg)
        self.play(LaggedStart(*[AnimationGroup(GrowArrow(s[0]), FadeIn(s[1])) for s in saidas], lag_ratio=0.3))
        self.play(LaggedStart(*[FadeIn(r, shift=LEFT * 0.2) for r in ramos], lag_ratio=0.3), run_time=2)

        atual = None
        for k, (p, e) in enumerate(zip(passos, explicacoes)):
            nova = tex(p, COR_DESTAQUE if k == len(passos) - 1 else WHITE, 32).move_to(P(0, -1.6))
            leg = self.legenda(e, leg, COR_DESTAQUE if k == len(passos) - 1 else GREY_A)
            if atual is None:
                self.play(Write(nova), run_time=2)
            else:
                self.play(ReplacementTransform(atual, nova), run_time=1.6)
            atual = nova
            self.wait(1.2)
        nota = Text("(notação de ponto: derivadas no tempo)", font_size=18, color=GREY_A).next_to(atual, DOWN, buff=0.2)
        self.play(Create(SurroundingRectangle(atual, color=COR_DESTAQUE, buff=0.12)), FadeIn(nota))
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 5
    def cena_laplace(self):
        self.titulo_cena("5 · Do tempo para a frequência (Laplace)")
        edo = tex(r"\ddot{v}_C + \frac{n^2 Z_0 + R}{n^2 R Z_0 C}\,\dot{v}_C + \frac{1}{LC}\,v_C = \frac{1}{C}\,\dot{i}_C",
                  WHITE, 32).move_to(P(0, 2.35))
        regras = tex(r"\mathcal{L}\{\ddot{v}_C\} = s^2 V_C(s),\quad \mathcal{L}\{\dot{v}_C\} = s\,V_C(s),\quad"
                     r"\mathcal{L}\{\dot{i}_C\} = s\,I_C(s)", GREY_A, 28).move_to(P(0, 1.4))
        r_regras = Text("(condições iniciais nulas)", font_size=18, color=GREY_A).next_to(regras, DOWN, buff=0.1)
        l1 = tex(r"s^2 V_C + s\,\frac{n^2 Z_0 + R}{n^2 R Z_0 C}\,V_C + \frac{1}{LC}\,V_C = \frac{s}{C}\,I_C", WHITE, 32)
        l2 = tex(r"V_C(s)\left[s^2 + s\,\frac{n^2 Z_0 + R}{n^2 R Z_0 C} + \frac{1}{LC}\right] = \frac{s}{C}\,I_C(s)",
                 WHITE, 32)
        l3 = tex(r"\frac{V_C(s)}{I_C(s)} = \frac{s/C}{s^2 + s\,\dfrac{n^2 Z_0 + R}{n^2 R Z_0 C} + \dfrac{1}{LC}}",
                 COR_DESTAQUE, 36)
        for m in (l1, l2):
            m.move_to(P(0, -0.2))
        l3.move_to(P(0, -1.5))

        leg = self.legenda("Partimos da equação diferencial da cavidade")
        self.play(Write(edo), run_time=1.5)
        leg = self.legenda("Transformada de Laplace: derivar no tempo vira multiplicar por s", leg)
        self.play(FadeIn(regras), FadeIn(r_regras))
        self.play(Write(l1), run_time=1.8)
        leg = self.legenda("Colocando V_C(s) em evidência", leg)
        self.play(ReplacementTransform(l1, l2), run_time=1.5)
        leg = self.legenda("Isolando a razão: a impedância vista pela corrente de excitação", leg, COR_DESTAQUE)
        self.play(TransformFromCopy(l2, l3), run_time=1.8)
        self.play(Create(SurroundingRectangle(l3, color=COR_DESTAQUE, buff=0.15)))
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 6
    def cena_canonica(self):
        self.titulo_cena("6 · Um filtro passa-banda de 2ª ordem")
        canon = tex_partes([(r"H_{BP}(s) = \frac{", WHITE), (r"K", COR_C), (r"\,s}{s^2 + ", WHITE),
                            (r"2\omega_{1/2}", COR_L), (r"\,s + ", WHITE), (r"\omega_0^2", COR_DESTAQUE),
                            (r"}", WHITE)], 36).move_to(P(0, 2.3))
        r_canon = Text("forma canônica do passa-banda de 2ª ordem", font_size=20, color=GREY_A
                       ).next_to(canon, DOWN, buff=0.12)
        cav = tex_partes([(r"\frac{V_C(s)}{I_C(s)} = \frac{", WHITE), (r"\tfrac{1}{C}", COR_C), (r"\,s}{s^2 + ", WHITE),
                          (r"\left[\tfrac{n^2 Z_0 + R}{n^2 R Z_0 C}\right]", COR_L), (r"\,s + ", WHITE),
                          (r"\tfrac{1}{LC}", COR_DESTAQUE), (r"}", WHITE)], 36).move_to(P(0, 0.6))
        r_cav = Text("cavidade", font_size=20, color=GREY_A).next_to(cav, DOWN, buff=0.12)
        mapas = VGroup(
            tex(r"\omega_0^2 = \frac{1}{LC} \;\Rightarrow\; \omega_0 = \frac{1}{\sqrt{LC}}", COR_DESTAQUE, 30),
            tex(r"2\omega_{1/2} = \frac{n^2 Z_0 + R}{n^2 R Z_0 C} = \frac{\omega_0}{Q}\quad\text{(largura de banda)}",
                COR_L, 30),
            tex(r"K = \frac{1}{C}\quad(s\ \text{no numerador: zero em}\ s = 0)", COR_C, 30),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(P(0, -1.75))

        leg = self.legenda("Compare com a forma padrão de um passa-banda de 2ª ordem")
        self.play(Write(canon), FadeIn(r_canon), run_time=1.5)
        self.play(Write(cav), FadeIn(r_cav), run_time=1.5)
        leg = self.legenda("Correspondência termo a termo", leg, COR_DESTAQUE)
        pares = [(5, 5, 0), (3, 3, 1), (1, 1, 2)]
        for i_c, i_v, i_m in pares:
            self.play(Indicate(canon[i_c], scale_factor=1.3), Indicate(cav[i_v], scale_factor=1.15))
            self.play(Write(mapas[i_m]), run_time=1.3)
        leg = self.legenda("A estrutura é idêntica: a cavidade é um filtro passa-banda centrado em ω₀", leg,
                           COR_DESTAQUE)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 7
    def cena_frequencia(self):
        self.titulo_cena("7 · Resposta em frequência da cavidade")
        yt, yb = 2.3, 0.75
        c, fios, rot, x = circuito_rebatido(yt, yb)
        circuito = VGroup(*c.values(), fios, *rot.values())
        self.play(FadeIn(circuito))

        ax = eixos_tempo(P(0, -1.55), 11.5, 2.3, [0, 3, 0.5], [0, 1.1, 0.5])
        r_ax = rotulo_eixo(ax, tex(r"|Z(j\omega)|\ /\ (R \,\|\, n^2 Z_0)", WHITE, 26))
        r_w = Text("ω/ω₀ →", font_size=18, color=COR_EIXO).next_to(ax, DOWN, buff=0.05).align_to(ax, RIGHT)
        curva = ax.plot(lambda w: abs(impedancia_norm(w)), x_range=[0.02, 3, 0.004], color=COR_DESTAQUE, stroke_width=4)
        w = ValueTracker(0.12)
        cursor = always_redraw(lambda: VGroup(
            Dot(ax.c2p(w.get_value(), abs(impedancia_norm(w.get_value()))), radius=0.09, color=WHITE),
            DashedLine(ax.c2p(w.get_value(), 0), ax.c2p(w.get_value(), 1.1), color=GREY_A, stroke_width=2)))

        leg = self.legenda("Magnitude da impedância vista pela corrente de excitação")
        self.play(Create(ax), FadeIn(r_ax), FadeIn(r_w))
        self.play(Create(curva), run_time=2)
        self.add(cursor)

        def destaque(chaves, cor, texto, pos):
            anim = [c[k].animate.set_stroke(cor, 8) for k in chaves]
            nota = Text(texto, font_size=20, color=cor).move_to(pos)
            return anim, nota

        # A) baixa frequência
        leg = self.legenda("ω → 0: o indutor vira curto (Z_L = jωL → 0) e drena toda a corrente", leg, COR_L)
        anim, nota_a = destaque(["L"], COR_L, "L ≈ curto ⇒ v_C → 0", P(-0.8, 0.3))
        self.play(*anim, FadeIn(nota_a))
        self.wait(1.2)
        self.play(c["L"].animate.set_stroke(COR_L, 4), FadeOut(nota_a))

        # C) ressonância
        leg = self.legenda("ω = ω₀: as susceptâncias de L e C se anulam; o par L∥C fica aberto", leg, COR_DESTAQUE)
        self.play(w.animate.set_value(1.0), run_time=3)
        self.play(c["L"].animate.set_opacity(0.25), c["C"].animate.set_opacity(0.25),
                  rot["L"].animate.set_opacity(0.25), rot["C"].animate.set_opacity(0.25),
                  c["R"].animate.set_stroke(COR_DESTAQUE, 8), c["Z"].animate.set_stroke(COR_DESTAQUE, 8))
        nota_c = tex(r"Z(j\omega_0) = R \,\|\, n^2 Z_0\quad\text{(máxima, puramente resistiva)}", COR_DESTAQUE, 26
                     ).move_to(P(0.6, 0.3))
        self.play(FadeIn(nota_c))
        meia = 1 / (2 * Q_CARREGADO)
        banda = DoubleArrow(ax.c2p(1 - meia, 0.707), ax.c2p(1 + meia, 0.707), buff=0, color=COR_L, stroke_width=3,
                            max_tip_length_to_length_ratio=0.25)
        r_banda = tex(r"2\omega_{1/2} = \omega_0/Q", COR_L, 24).next_to(banda, RIGHT, buff=0.15)
        leg = self.legenda("Toda a corrente passa pelas resistências: tensão máxima na cavidade", leg, COR_DESTAQUE)
        self.play(GrowFromCenter(banda), FadeIn(r_banda))
        self.wait(1.5)
        self.play(FadeOut(nota_c), c["L"].animate.set_opacity(1), c["C"].animate.set_opacity(1),
                  rot["L"].animate.set_opacity(1), rot["C"].animate.set_opacity(1),
                  c["R"].animate.set_stroke(COR_R, 4), c["Z"].animate.set_stroke(COR_RF, 4))

        # B) alta frequência
        leg = self.legenda("ω → ∞: o capacitor vira curto (Z_C = 1/jωC → 0) e drena toda a corrente", leg, COR_C)
        self.play(w.animate.set_value(2.9), run_time=3)
        anim, nota_b = destaque(["C"], COR_C, "C ≈ curto ⇒ v_C → 0", P(-0.8, 0.3))
        self.play(*anim, FadeIn(nota_b))
        self.wait(1.2)
        leg = self.legenda("Nula em 0, máxima em ω₀, nula em ∞: um filtro passa-banda de 2ª ordem", leg, COR_DESTAQUE)
        self.play(c["C"].animate.set_stroke(COR_C, 4), FadeOut(nota_b), w.animate.set_value(1.0), run_time=2)
        self.wait(1.5)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo")
        linhas = [
            (r"\text{Cavidade metálica}", r"\text{Circuito } RLC \text{ paralelo}", COR_DESTAQUE),
            (r"\text{Acoplador / antena}", r"\text{Transformador } 1:n", COR_ACOPLA),
            (r"\text{Potência de RF externa}", r"\text{Fonte } I'_{rf} \text{ com } Z_0", COR_RF),
            (r"\text{Feixe relativístico}", r"\text{Fonte de corrente } I_b", COR_FEIXE),
        ]
        grupo = VGroup()
        for a, b, cor in linhas:
            grupo.add(VGroup(tex(a, WHITE, 30), tex(r"\longrightarrow", GREY_A, 30), tex(b, cor, 30)
                             ).arrange(RIGHT, buff=0.35))
        grupo.arrange(DOWN, aligned_edge=LEFT, buff=0.35).move_to(P(0, 1.0))
        cadeia = Text("Maxwell 3D  →  EDO linear de 2ª ordem  →  Z(s) passa-banda  →  projeto do controle LLRF",
                      font_size=22, color=COR_DESTAQUE).move_to(P(0, -1.6))
        self.play(LaggedStart(*[FadeIn(g, shift=RIGHT * 0.2) for g in grupo], lag_ratio=0.35), run_time=3)
        self.play(Write(cadeia), run_time=2)
        self.wait(3)
        self.limpar()
