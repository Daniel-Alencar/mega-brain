# -*- coding: utf-8 -*-
"""
Amostragem e Aliasing: o que o ADC guarda e o que ele joga fora
===============================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/3 - Amostragem e Aliasing/amostragem_aliasing.py" AmostragemAliasing   # rascunho
    manim -pqh "src/3 - Amostragem e Aliasing/amostragem_aliasing.py" AmostragemAliasing   # final

Requer LaTeX (MathTex).

Roteiro (segue "docs/3 - Amostragem e Aliasing/Amostragem e Aliasing"):
    Abertura
    Cena 1 - A ambiguidade: a mesma sequência serve a infinitas ondas
    Cena 2 - De onde vem: amostrar é multiplicar por um pente de impulsos
    Cena 3 - O critério de Nyquist: quando as réplicas se encostam
    Cena 4 - A regra da dobra e as zonas de Nyquist
    Cena 5 - O filtro anti-aliasing: a única defesa, e ela é analógica
    Cena 6 - Quantização: o segundo erro, independente do primeiro
    Cena 7 - Reconstrução: interpolação sinc, ZOH e o droop
    Cena 8 - Sub-amostragem deliberada: quando o aliasing é a ferramenta
    Resumo

Exemplo numérico usado nas cenas 1 a 7:
    f_s = 10 kHz (T = 0,1 ms), sinal útil de 0 a 4 kHz.
A cena 8 muda de escala: portadora de 500 MHz amostrada a 80 MSps.

Layout: a tela é dividida em faixas fixas para que nada se sobreponha.
    y > 3.0          : título da cena (canto superior esquerdo)
    [Y_BASE, Y_TOPO] : área de desenho
    y ~ -3.65        : narração, uma linha por vez
"""

import numpy as np
from manim import *

# Paleta didática (mesma convenção das outras animações do repositório)
COR_SINAL = BLUE          # sinal útil / banda base
COR_AMOSTRA = WHITE       # amostras, pente de impulsos
COR_ALIAS = RED           # aliasing, réplica invasora, erro
COR_REPLICA = PURPLE_B    # réplicas do espectro
COR_NYQ = ORANGE          # limite de Nyquist (f_s/2)
COR_FILTRO = PINK         # filtros analógicos (anti-aliasing e suavização)
COR_DIG = TEAL            # quantização / domínio digital
COR_OK = GREEN            # reconstrução correta
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}

# Faixas de layout (a tela vai de -4 a 4 em y e de -7.1 a 7.1 em x)
Y_TOPO = 2.70
Y_BASE = -2.55
LARG_MAX = 12.8

FS = 10.0        # taxa de amostragem do exemplo, em kHz
F_MAX = 4.0      # topo da banda útil, em kHz


# =============================================================================
# Utilitários de construção
# =============================================================================
def P(x, y):
    return np.array([x, y, 0.0])


def ajustar(m, largura=LARG_MAX):
    """Encolhe o mobject se ele for largo demais para a tela."""
    if m.width > largura:
        m.scale(largura / m.width)
    return m


def tex(s, cor=WHITE, tamanho=34):
    return MathTex(s, color=cor, font_size=tamanho)


def txt(s, tamanho=22, cor=GREY_A, **kw):
    return Text(s, font_size=tamanho, color=cor, **kw)


def tex_partes(partes, tamanho=34):
    """Fórmula multicolorida. partes = [(tex, cor), ...]."""
    m = MathTex(*[p[0] for p in partes], font_size=tamanho)
    for sub, p in zip(m, partes):
        sub.set_color(p[1])
    return m


def fio(pontos, cor=WHITE, largura=3):
    g = VGroup(*[Line(pontos[k], pontos[k + 1], color=cor, stroke_width=largura)
                 for k in range(len(pontos) - 2)])
    g.add(Arrow(pontos[-2], pontos[-1], buff=0, color=cor, stroke_width=largura,
                max_tip_length_to_length_ratio=0.3, max_stroke_width_to_length_ratio=10))
    return g


def linha(pontos, cor=WHITE, largura=3):
    return VMobject().set_points_as_corners(pontos).set_stroke(cor, largura)


def caixa(rotulo, largura=1.6, altura=0.7, cor=WHITE, tamanho=20):
    r = RoundedRectangle(corner_radius=0.08, width=largura, height=altura, color=cor, stroke_width=3)
    return VGroup(r, Text(rotulo, color=cor, font_size=tamanho).move_to(r))


def caixa_tex(rotulo, largura=1.0, altura=0.7, cor=WHITE, tamanho=28):
    r = RoundedRectangle(corner_radius=0.08, width=largura, height=altura, color=cor, stroke_width=3)
    return VGroup(r, tex(rotulo, cor, tamanho).move_to(r))


def multiplicador(cor=WHITE, raio=0.3):
    c = Circle(radius=raio, color=cor, stroke_width=3)
    d = raio * 0.62
    x = VGroup(Line(P(-d, -d), P(d, d), color=cor, stroke_width=3),
               Line(P(-d, d), P(d, -d), color=cor, stroke_width=3))
    return VGroup(c, x.move_to(c))


def eixos(centro, largura, altura, x_range, y_range):
    return Axes(x_range=x_range, y_range=y_range, x_length=largura, y_length=altura,
                axis_config=EIXO_CFG).move_to(centro)


def rotulo_eixo(ax, mob, buff=0.08):
    return mob.next_to(ax, UP, buff=buff).align_to(ax, LEFT)


def polilinha(ax, xs, ys, cor, largura=3):
    return linha([ax.c2p(a, b) for a, b in zip(xs, ys)], cor, largura)


def curva(ax, func, cor, largura=3, n=600, x0=None, x1=None):
    a = ax.x_range[0] if x0 is None else x0
    b = ax.x_range[1] if x1 is None else x1
    xs = np.linspace(a, b, n)
    return polilinha(ax, xs, func(xs), cor, largura)


def haste(ax, x, y, cor, raio=0.075, largura=2):
    """Amostra: traço vertical com bolinha na ponta."""
    return VGroup(Line(ax.c2p(x, 0), ax.c2p(x, y), color=cor, stroke_width=largura),
                  Dot(ax.c2p(x, y), radius=raio, color=cor))


def raia(ax, f, altura, cor, largura=6):
    return Arrow(ax.c2p(f, 0), ax.c2p(f, altura), buff=0, color=cor, stroke_width=largura,
                 max_tip_length_to_length_ratio=0.22, max_stroke_width_to_length_ratio=14)


def triangulo(ax, centro, meia_base, altura, cor, opacidade=0.45):
    """Espectro esquemático de uma banda: triângulo isósceles sobre o eixo."""
    return Polygon(ax.c2p(centro - meia_base, 0), ax.c2p(centro, altura),
                   ax.c2p(centro + meia_base, 0),
                   color=cor, stroke_width=2).set_fill(cor, opacity=opacidade)


def meio_triangulo(ax, f0, f1, altura, cor, opacidade=0.45):
    """Metade direita de um espectro em banda base, para eixos que começam em 0."""
    return Polygon(ax.c2p(f0, 0), ax.c2p(f0, altura), ax.c2p(f1, 0),
                   color=cor, stroke_width=2).set_fill(cor, opacity=opacidade)


def banda(ax, centro, meia_base, altura, cor, opacidade=0.5):
    """Espectro esquemático de uma faixa estreita: trapézio sobre o eixo."""
    c = ax.c2p(centro, 0)
    dx = (ax.c2p(centro + meia_base, 0) - c)
    dy = (ax.c2p(centro, altura) - c)
    return Polygon(c - dx, c - dx * 0.45 + dy, c + dx * 0.45 + dy, c + dx,
                   color=cor, stroke_width=2).set_fill(cor, opacity=opacidade)


def marcar_x(ax, valores, rotulos, tamanho=16, buff=0.12, cor=COR_EIXO):
    return VGroup(*[Text(r, font_size=tamanho, color=cor).next_to(ax.c2p(v, 0), DOWN, buff=buff)
                    for v, r in zip(valores, rotulos)])


def tracejada(a, b, cor, largura=2, pedaco=0.12):
    return DashedLine(a, b, color=cor, stroke_width=largura, dash_length=pedaco)


def dobrar(f, fs=FS):
    """Regra da dobra: para onde uma frequência f aparece ao amostrar a fs."""
    return np.abs(f - fs * np.round(np.asarray(f, dtype=float) / fs))


def escada(xs, ys):
    """Pontos de uma função em degraus (zero-order hold) para polilinha."""
    px, py = [], []
    for k in range(len(xs) - 1):
        px += [xs[k], xs[k + 1]]
        py += [ys[k], ys[k]]
    px.append(xs[-1])
    py.append(ys[-1])
    return px, py


def quantizar(y, bits, fundo=1.2):
    """Quantização uniforme de y para `bits` bits na faixa ±fundo."""
    passo = 2 * fundo / 2 ** bits
    return np.clip(np.round(y / passo) * passo, -fundo, fundo)


# =============================================================================
# Cena
# =============================================================================
class AmostragemAliasing(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_ambiguidade()
        self.cena_replicas()
        self.cena_nyquist()
        self.cena_dobra()
        self.cena_filtro()
        self.cena_quantizacao()
        self.cena_reconstrucao()
        self.cena_subamostragem()
        self.cena_resumo()

    # ------------------------------------------------------------- utilidades
    def titulo_cena(self, texto):
        t = Text(texto, font_size=32, weight=BOLD).to_corner(UL, buff=0.35)
        ln = Line(t.get_corner(DL), t.get_corner(DR), color=COR_EIXO,
                  stroke_width=2).shift(DOWN * 0.12)
        self.play(Write(t), Create(ln), run_time=1.0)
        self.wait(0.4)
        return VGroup(t, ln)

    def trocar_titulo(self, titulo, texto):
        novo = Text(texto, font_size=32, weight=BOLD).to_corner(UL, buff=0.35)
        ln = Line(novo.get_corner(DL), novo.get_corner(DR), color=COR_EIXO,
                  stroke_width=2).shift(DOWN * 0.12)
        self.play(Transform(titulo[0], novo), Transform(titulo[1], ln), run_time=0.8)

    def legenda(self, texto, anterior=None, cor=GREY_A, pausa=None):
        """Narração no rodapé. Espera o tempo de leitura antes de prosseguir."""
        nova = ajustar(Text(texto, font_size=24, color=cor), 13.2).to_edge(DOWN, buff=0.35)
        if anterior is None:
            self.play(FadeIn(nova, shift=UP * 0.2), run_time=0.8)
        else:
            self.play(FadeOut(anterior, shift=UP * 0.2), FadeIn(nova, shift=UP * 0.2), run_time=0.8)
        self.wait(pausa if pausa is not None else 0.5 + 0.022 * len(texto))
        return nova

    def limpar(self):
        for m in self.mobjects:
            m.clear_updaters()
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.9)
        self.wait(0.25)

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Amostragem e Aliasing", font_size=60, weight=BOLD)
        sub = txt("o que o ADC guarda, o que ele joga fora, e como escolher a taxa", 28)
        cadeia = VGroup(txt("onda contínua", 20, COR_SINAL), tex(r"\rightarrow", GREY_A, 30),
                        caixa("ADC", 1.2, 0.6, COR_AMOSTRA, 20), tex(r"\rightarrow", GREY_A, 30),
                        tex(r"x[n]", COR_AMOSTRA, 30)).arrange(RIGHT, buff=0.3)
        nota = txt("dois erros independentes nascem aqui: aliasing e quantização", 22, GREY_B)
        g = VGroup(titulo, sub, cadeia, nota).arrange(DOWN, buff=0.5)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(cadeia, shift=UP * 0.2))
        self.play(FadeIn(nota, shift=UP * 0.2))
        self.wait(1.8)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_ambiguidade(self):
        """O fato central: a sequência não identifica a frequência."""
        self.titulo_cena("1 · A mesma sequência serve a infinitas ondas")

        ax = eixos(P(0, 1.15), 12.3, 2.4, [0, 1.0, 0.1], [-1.4, 1.4, 1])
        marcas = marcar_x(ax, [0, 0.2, 0.4, 0.6, 0.8, 1.0], ["0", "0,2", "0,4", "0,6", "0,8", "1,0"])
        r_t = txt("tempo [ms]  →", 18, COR_EIXO).next_to(ax, DOWN, buff=0.38).align_to(ax, RIGHT)

        ts = np.arange(11) / 10.0                       # T = 0,1 ms  (f_s = 10 kHz)
        ys = np.cos(TAU * ts)
        amostras = VGroup(*[haste(ax, t, y, COR_AMOSTRA, 0.085) for t, y in zip(ts, ys)])

        c1 = curva(ax, lambda t: np.cos(TAU * 1 * t), COR_SINAL, 4)
        c9 = curva(ax, lambda t: np.cos(TAU * 9 * t), COR_ALIAS, 3, n=1400)
        c11 = curva(ax, lambda t: np.cos(TAU * 11 * t), COR_REPLICA, 3, n=1600)

        rot1 = tex(r"1\ \text{kHz}", COR_SINAL, 28).move_to(P(-5.6, 2.45))
        rot9 = tex(r"9\ \text{kHz}", COR_ALIAS, 28).move_to(P(-2.6, 2.45))
        rot11 = tex(r"11\ \text{kHz}", COR_REPLICA, 28).move_to(P(0.6, 2.45))
        taxa = tex(r"f_s = 10\ \text{kHz}", COR_AMOSTRA, 28).move_to(P(5.0, 2.45))

        leg = self.legenda("Amostrar é guardar o valor em t = nT — e não guardar mais nada")
        self.play(Create(ax), FadeIn(marcas), FadeIn(r_t))
        self.play(Create(c1), run_time=1.6)
        self.play(FadeIn(rot1), FadeIn(taxa))
        self.play(LaggedStart(*[GrowFromPoint(a, ax.c2p(t, 0)) for a, t in zip(amostras, ts)],
                              lag_ratio=0.12), run_time=2.0)
        leg = self.legenda("Onze números. Entre eles, o ADC não mediu nada — e nada pode afirmar", leg)

        self.play(Create(c9), run_time=2.0)
        self.play(FadeIn(rot9))
        leg = self.legenda("Esta onda de 9 kHz passa exatamente pelos mesmos onze pontos", leg, COR_ALIAS)
        self.play(Create(c11), run_time=2.0)
        self.play(FadeIn(rot11))
        leg = self.legenda("E a de 11 kHz também. E infinitas outras", leg, COR_REPLICA)

        self.play(FadeOut(VGroup(c1, c9, c11, rot1, rot9, rot11, taxa,
                                 ax, marcas, r_t, amostras)))

        conta = VGroup(
            tex(r"\cos\!\left(2\pi \cdot \tfrac{9n}{10}\right) = "
                r"\cos\!\left(2\pi n - 2\pi \cdot \tfrac{n}{10}\right) = "
                r"\cos\!\left(2\pi \cdot \tfrac{n}{10}\right)", WHITE, 40),
            txt("o cosseno tem período 2π: o giro inteiro de 2πn não muda nada", 22, GREY_B),
        ).arrange(DOWN, buff=0.45).move_to(P(0, 1.3))
        geral = tex(r"f \quad \text{e} \quad f + k\,f_s \quad "
                    r"\text{dão a mesma sequência, para todo } k \text{ inteiro}", WHITE, 34
                    ).move_to(P(0, -0.55))

        leg = self.legenda("A razão é aritmética de arco, não defeito do conversor", leg)
        self.play(Write(conta[0]), run_time=1.8)
        self.play(FadeIn(conta[1], shift=UP * 0.2))
        self.wait(0.6)
        self.play(Write(geral), run_time=1.6)
        leg = self.legenda("O ADC não erra cada medida: ele perde a identidade da frequência", leg, COR_ALIAS)
        nome = txt("é esse apagamento que se chama aliasing", 26, COR_ALIAS).move_to(P(0, -1.85))
        self.play(FadeIn(nome, shift=UP * 0.2))
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 2
    def cena_replicas(self):
        """O mesmo fato no domínio da frequência: réplicas a cada f_s."""
        titulo = self.titulo_cena("2 · Amostrar é multiplicar por um pente de impulsos")

        # --- parte A: no tempo -------------------------------------------------
        larg, alt = 3.5, 1.25
        xs = [-4.75, -0.25, 4.25]
        ax1 = eixos(P(xs[0], 0.9), larg, alt, [0, 1, 0.5], [-1.3, 1.3, 1])
        ax2 = eixos(P(xs[1], 0.9), larg, alt, [0, 1, 0.5], [0, 1.3, 1])
        ax3 = eixos(P(xs[2], 0.9), larg, alt, [0, 1, 0.5], [-1.3, 1.3, 1])

        onda = curva(ax1, lambda t: np.cos(TAU * t), COR_SINAL, 3)
        ts = np.arange(0, 1.001, 0.1)
        pente = VGroup(*[raia(ax2, t, 1.0, COR_AMOSTRA, 4) for t in ts])
        prod = VGroup(*[haste(ax3, t, np.cos(TAU * t), COR_AMOSTRA, 0.06) for t in ts])

        n1 = tex(r"x(t)", COR_SINAL, 26).next_to(ax1, UP, buff=0.12)
        n2 = tex(r"\sum_n \delta(t - nT)", COR_AMOSTRA, 26).next_to(ax2, UP, buff=0.12)
        n3 = tex(r"x_s(t)", COR_AMOSTRA, 26).next_to(ax3, UP, buff=0.12)
        op1 = tex(r"\times", GREY_A, 40).move_to(P(-2.5, 0.9))
        op2 = tex(r"=", GREY_A, 40).move_to(P(2.0, 0.9))

        leg = self.legenda("No tempo, a amostragem é um produto por um trem de impulsos")
        self.play(Create(ax1), Create(ax2), Create(ax3), FadeIn(n1), FadeIn(n2), FadeIn(n3))
        self.play(Create(onda), run_time=1.2)
        self.play(FadeIn(op1), LaggedStart(*[GrowArrow(r) for r in pente], lag_ratio=0.08), run_time=1.4)
        self.play(FadeIn(op2), LaggedStart(*[FadeIn(h) for h in prod], lag_ratio=0.08), run_time=1.4)
        leg = self.legenda("Produto no tempo é convolução na frequência — e aí está a surpresa", leg)

        self.play(FadeOut(VGroup(ax1, ax2, ax3, onda, pente, prod, n1, n2, n3, op1, op2)))

        # --- parte B: na frequência -------------------------------------------
        self.trocar_titulo(titulo, "2 · Na frequência: o espectro se replica")
        axf = eixos(P(0, 0.35), 12.4, 2.3, [-6, 30, 2], [0, 1.15, 1])
        r_f = txt("frequência [kHz]  →", 18, COR_EIXO).next_to(axf, DOWN, buff=0.45).align_to(axf, RIGHT)
        marcas = marcar_x(axf, [0, 10, 20, 30], ["0", "10", "20", "30"], buff=0.14)

        base = triangulo(axf, 0, F_MAX, 1.0, COR_SINAL)
        rot_base = txt("espectro do sinal", 19, COR_SINAL).next_to(axf.c2p(0, 1.0), UP, buff=0.12)
        reps = VGroup(*[triangulo(axf, k * FS, F_MAX, 1.0, COR_REPLICA) for k in (1, 2)])
        rots = VGroup(tex(r"f_s", COR_REPLICA, 24).next_to(axf.c2p(FS, 1.0), UP, buff=0.12),
                      tex(r"2f_s", COR_REPLICA, 24).next_to(axf.c2p(2 * FS, 1.0), UP, buff=0.12))

        formula = tex(r"X_s(f) = f_s \sum_{k} X(f - k f_s)", WHITE, 38).move_to(P(-3.2, -1.65))
        nota = txt("o espectro de um sinal amostrado é periódico, com período f_s",
                   21, GREY_B).move_to(P(3.4, -1.65))

        leg = self.legenda("A transformada de um pente de impulsos é outro pente, espaçado de f_s", leg)
        self.play(Create(axf), FadeIn(marcas), FadeIn(r_f))
        self.play(DrawBorderThenFill(base), FadeIn(rot_base), run_time=1.2)
        leg = self.legenda("Convoluir com esse pente copia o espectro inteiro em cada múltiplo de f_s", leg)
        self.play(LaggedStart(*[DrawBorderThenFill(r) for r in reps], lag_ratio=0.35), run_time=1.8)
        self.play(FadeIn(rots))
        self.play(Write(formula), run_time=1.4)
        self.play(FadeIn(nota, shift=UP * 0.2))
        leg = self.legenda("As réplicas são as infinitas ondas da cena 1, agora visíveis", leg)
        self.wait(1.0)
        self.limpar()

    # ================================================================== CENA 3
    def cena_nyquist(self):
        """O critério: as réplicas não podem se encostar."""
        self.titulo_cena("3 · O critério de Nyquist-Shannon")

        axf = eixos(P(0, 0.75), 12.4, 2.1, [-6, 30, 2], [0, 1.15, 1])
        r_f = txt("frequência [kHz]  →", 18, COR_EIXO).next_to(axf, DOWN, buff=0.42).align_to(axf, RIGHT)
        fs_t = ValueTracker(14.0)

        base = triangulo(axf, 0, F_MAX, 1.0, COR_SINAL)
        reps = always_redraw(lambda: VGroup(*[
            triangulo(axf, k * fs_t.get_value(), F_MAX, 1.0, COR_REPLICA)
            for k in (1, 2) if k * fs_t.get_value() + F_MAX <= 30]))
        nyq = always_redraw(lambda: tracejada(
            axf.c2p(fs_t.get_value() / 2, 0), axf.c2p(fs_t.get_value() / 2, 1.1), COR_NYQ, 3))
        rot_nyq = always_redraw(lambda: tex(r"f_s/2", COR_NYQ, 24).next_to(
            axf.c2p(fs_t.get_value() / 2, 1.1), UP, buff=0.1))
        rot_fmax = tex(r"f_{max} = 4", COR_SINAL, 24).next_to(axf.c2p(F_MAX, 0), DOWN, buff=0.14)

        painel = always_redraw(lambda: VGroup(
            tex(rf"f_s = {fs_t.get_value():.0f}\ \text{{kHz}}", COR_AMOSTRA, 32),
            tex(rf"2f_{{max}} = 8\ \text{{kHz}}", COR_SINAL, 28),
        ).arrange(RIGHT, buff=0.8).move_to(P(0, -1.15)))

        leg = self.legenda("A réplica em f_s começa em f_s − f_max: é ela que se aproxima da banda")
        self.play(Create(axf), FadeIn(r_f), FadeIn(rot_fmax))
        self.play(DrawBorderThenFill(base), run_time=0.9)
        self.add(reps, nyq, rot_nyq)
        self.play(FadeIn(painel))
        self.wait(0.6)

        leg = self.legenda("Baixando f_s, a réplica caminha para a esquerda", leg)
        self.play(fs_t.animate.set_value(10.0), run_time=2.0)
        self.wait(0.5)
        leg = self.legenda("Em f_s = 2·f_max as duas se encostam exatamente em f_max: o caso-limite", leg, COR_NYQ)
        self.play(fs_t.animate.set_value(8.0), run_time=2.0)
        self.wait(0.8)

        leg = self.legenda("Abaixo disso elas se sobrepõem — e as bandas se somam", leg, COR_ALIAS)
        self.play(fs_t.animate.set_value(6.0), run_time=2.0)
        sobrepos = Polygon(axf.c2p(2, 0), axf.c2p(3, 0.75), axf.c2p(4, 0),
                           color=COR_ALIAS, stroke_width=3).set_fill(COR_ALIAS, opacity=0.6)
        marca_sobre = txt("aqui as duas se somaram:\nnão há como separá-las", 20, COR_ALIAS,
                          line_spacing=0.85).move_to(P(-1.9, -1.95))
        self.play(DrawBorderThenFill(sobrepos), FadeIn(marca_sobre, shift=UP * 0.2))
        self.wait(1.0)

        painel.clear_updaters()
        self.play(FadeOut(sobrepos), FadeOut(marca_sobre), FadeOut(painel),
                  fs_t.animate.set_value(12.0), run_time=1.6)
        crit = VGroup(tex(r"f_s > 2 f_{max}", WHITE, 48),
                      txt("satisfeito o critério, o sinal contínuo pode ser reconstruído\n"
                          "integralmente a partir das amostras — não se perde nada",
                          21, GREY_B, line_spacing=0.9)).arrange(DOWN, buff=0.35).move_to(P(0, -1.85))
        caixa_crit = SurroundingRectangle(crit[0], color=COR_OK, buff=0.22, corner_radius=0.1)
        leg = self.legenda("Com folga, as réplicas ficam separadas e a banda original fica intacta", leg, COR_OK)
        self.play(Write(crit[0]), Create(caixa_crit), run_time=1.4)
        self.play(FadeIn(crit[1], shift=UP * 0.2))
        self.wait(1.4)
        self.limpar()

    # ================================================================== CENA 4
    def cena_dobra(self):
        """Onde cada frequência aparece quando o critério é violado."""
        self.titulo_cena("4 · A regra da dobra")

        ax = eixos(P(-1.75, 0.55), 8.3, 2.7, [0, 25, 5], [0, 5.6, 1])
        r_x = txt("frequência real [kHz]  →", 17, COR_EIXO).next_to(ax, DOWN, buff=0.42).align_to(ax, RIGHT)
        r_y = txt("frequência aparente [kHz]", 17, COR_EIXO)
        rotulo_eixo(ax, r_y, 0.14)
        mx = marcar_x(ax, [0, 5, 10, 15, 20, 25], ["0", "5", "10", "15", "20", "25"], 15, 0.12)
        my = VGroup(*[Text(str(v), font_size=15, color=COR_EIXO).next_to(ax.c2p(0, v), LEFT, buff=0.12)
                      for v in (5,)])

        fs_meio = tracejada(ax.c2p(0, FS / 2), ax.c2p(25, FS / 2), COR_NYQ, 2)
        rot_meio = tex(r"f_s/2 = 5", COR_NYQ, 22).next_to(ax.c2p(25, FS / 2), UP, buff=0.1).shift(LEFT * 0.55)

        zonas = VGroup()
        rotz = VGroup()
        for k, nome in enumerate(["1ª zona", "2ª", "3ª", "4ª", "5ª"]):
            a, b = k * FS / 2, min((k + 1) * FS / 2, 25)
            cinza = GREY_E if k % 2 == 0 else "#1b2430"
            zonas.add(Polygon(ax.c2p(a, 0), ax.c2p(b, 0), ax.c2p(b, 5.6), ax.c2p(a, 5.6),
                              stroke_width=0).set_fill(cinza, opacity=0.65))
            rotz.add(Text(nome, font_size=14, color=GREY_B).move_to(ax.c2p((a + b) / 2, 5.25)))

        xs = np.linspace(0, 25, 1200)
        mapa = polilinha(ax, xs, dobrar(xs), COR_ALIAS, 4)
        formula = tex(r"f_{ap} = \big|\, f - f_s \cdot \mathrm{round}(f/f_s) \,\big|", WHITE, 32
                      ).move_to(P(-1.75, -2.2))

        tabela = VGroup(
            txt("f", 22, COR_EIXO), txt("f aparente", 22, COR_EIXO),
            tex(r"1", WHITE, 26), tex(r"1", COR_SINAL, 26),
            tex(r"4", WHITE, 26), tex(r"4", COR_SINAL, 26),
            tex(r"6", WHITE, 26), tex(r"4", COR_ALIAS, 26),
            tex(r"9", WHITE, 26), tex(r"1", COR_ALIAS, 26),
            tex(r"11", WHITE, 26), tex(r"1", COR_ALIAS, 26),
            tex(r"21", WHITE, 26), tex(r"1", COR_ALIAS, 26),
        ).arrange_in_grid(rows=7, cols=2, buff=(0.5, 0.26)).move_to(P(4.65, 0.75))
        titulo_tab = txt("com f_s = 10 kHz", 20, GREY_B).next_to(tabela, UP, buff=0.3)

        leg = self.legenda("Violado o critério, ainda se sabe exatamente onde cada frequência vai cair")
        self.play(FadeIn(zonas), Create(ax), FadeIn(mx), FadeIn(my), FadeIn(r_x), FadeIn(r_y))
        self.play(Create(fs_meio), FadeIn(rot_meio), FadeIn(rotz))
        self.play(Write(formula), run_time=1.3)
        leg = self.legenda("Subtrai-se o múltiplo de f_s mais próximo e toma-se o módulo", leg)
        self.play(Create(mapa), run_time=2.6)
        self.play(FadeIn(titulo_tab), FadeIn(tabela[0]), FadeIn(tabela[1]))

        f_t = ValueTracker(1.0)
        ponto = always_redraw(lambda: Dot(ax.c2p(f_t.get_value(), float(dobrar(f_t.get_value()))),
                                         radius=0.09, color=COR_AMOSTRA))
        guia_v = always_redraw(lambda: tracejada(
            ax.c2p(f_t.get_value(), 0), ax.c2p(f_t.get_value(), float(dobrar(f_t.get_value()))),
            COR_AMOSTRA, 2, 0.08))
        guia_h = always_redraw(lambda: tracejada(
            ax.c2p(0, float(dobrar(f_t.get_value()))),
            ax.c2p(f_t.get_value(), float(dobrar(f_t.get_value()))), COR_AMOSTRA, 2, 0.08))
        self.add(ponto, guia_v, guia_h)

        leg = self.legenda("A frequência real sobe sem parar; a aparente vai e volta, como uma sanfona", leg)
        for k, destino in enumerate([4, 6, 9, 11, 21]):
            self.play(f_t.animate.set_value(destino), run_time=1.3)
            self.play(FadeIn(tabela[2 + 2 * k], shift=RIGHT * 0.2),
                      FadeIn(tabela[3 + 2 * k], shift=RIGHT * 0.2), run_time=0.5)
            self.wait(0.35)
        self.play(FadeIn(tabela[12], shift=RIGHT * 0.2), FadeIn(tabela[13], shift=RIGHT * 0.2), run_time=0.5)

        leg = self.legenda("Todas as zonas se dobram sobre a primeira — e as pares chegam invertidas", leg, COR_ALIAS)
        inv = VGroup(*[Line(ax.c2p(a, 0.35), ax.c2p(b, 0.35), color=COR_ALIAS, stroke_width=3)
                       for a, b in [(5, 10), (15, 20)]])
        setas_inv = VGroup(*[Arrow(ax.c2p(b, 0.35), ax.c2p(a, 0.35), buff=0, color=COR_ALIAS,
                                   stroke_width=4, max_tip_length_to_length_ratio=0.1)
                             for a, b in [(5, 10), (15, 20)]])
        self.play(Create(inv), Create(setas_inv), run_time=1.0)
        nota = txt("numa banda modulada, inverter o espectro troca o sinal da fase",
                   20, COR_ALIAS).move_to(P(2.2, -2.75))
        self.play(FadeIn(nota, shift=UP * 0.2))
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 5
    def cena_filtro(self):
        """A única defesa possível, e ela é analógica."""
        titulo = self.titulo_cena("5 · O filtro anti-aliasing")

        cadeia = VGroup(txt("entrada", 20, GREY_A), tex(r"\rightarrow", GREY_A, 28),
                        caixa("passa-baixa\nanalógico", 2.3, 0.85, COR_FILTRO, 18),
                        tex(r"\rightarrow", GREY_A, 28), caixa("ADC", 1.1, 0.85, COR_AMOSTRA, 20),
                        tex(r"\rightarrow", GREY_A, 28), txt("digital", 20, COR_DIG)
                        ).arrange(RIGHT, buff=0.26).move_to(P(0, 2.2))

        axf = eixos(P(0, 0.2), 12.0, 2.0, [0, 14, 2], [0, 1.2, 1])
        r_f = txt("frequência [kHz]  →", 18, COR_EIXO).next_to(axf, DOWN, buff=0.45).align_to(axf, RIGHT)
        mx = marcar_x(axf, [0, 5, 10], ["0", "5", "10"], 16, 0.14)
        util = meio_triangulo(axf, 0, F_MAX, 0.95, COR_SINAL)
        rot_util = txt("sinal útil, 0 a 4 kHz", 19, COR_SINAL).next_to(axf.c2p(2, 0), DOWN, buff=0.45)
        nyq = tracejada(axf.c2p(5, 0), axf.c2p(5, 1.15), COR_NYQ, 3)
        rot_nyq = tex(r"f_s/2", COR_NYQ, 22).next_to(axf.c2p(5, 1.15), UP, buff=0.08)
        intru = raia(axf, 7, 0.75, COR_ALIAS, 6)
        rot_intru = txt("interferência\nem 7 kHz", 19, COR_ALIAS, line_spacing=0.85
                        ).next_to(axf.c2p(7, 0.75), UR, buff=0.1)

        leg = self.legenda("Sinal útil até 4 kHz, amostrado a 10 kHz — e uma interferência em 7 kHz")
        self.play(FadeIn(cadeia[0]), FadeIn(cadeia[1]), FadeIn(cadeia[4]), FadeIn(cadeia[5]),
                  FadeIn(cadeia[6]), Create(axf), FadeIn(mx), FadeIn(r_f))
        self.play(DrawBorderThenFill(util), FadeIn(rot_util), Create(nyq), FadeIn(rot_nyq))
        self.play(GrowArrow(intru), FadeIn(rot_intru))
        leg = self.legenda("Sem filtro, ela se dobra para |7 − 10| = 3 kHz: dentro da banda útil", leg, COR_ALIAS)

        arco = ArcBetweenPoints(axf.c2p(7, 0.78), axf.c2p(3, 0.78), angle=-PI / 2.2,
                                color=COR_ALIAS, stroke_width=3)
        dobrada = raia(axf, 3, 0.75, COR_ALIAS, 6)
        self.play(Create(arco), run_time=1.0)
        self.play(TransformFromCopy(intru, dobrada), run_time=1.0)
        perdido = txt("agora está somada ao sinal: nenhum processamento digital a separa",
                      21, COR_ALIAS).move_to(P(0, -1.75))
        self.play(FadeIn(perdido, shift=UP * 0.2))
        self.wait(0.8)

        leg = self.legenda("A defesa tem de agir antes da amostragem — ou seja, no analógico", leg, COR_FILTRO)
        self.play(FadeIn(cadeia[2], shift=DOWN * 0.2), FadeIn(cadeia[3]))
        resp = polilinha(axf, np.linspace(0, 14, 400),
                         1.05 / np.sqrt(1 + (np.linspace(0, 14, 400) / 4.6) ** 12), COR_FILTRO, 3)
        self.play(Create(resp), run_time=1.2)
        self.play(FadeOut(arco), FadeOut(dobrada), FadeOut(perdido),
                  intru.animate.scale(0.08, about_point=axf.c2p(7, 0)).set_opacity(0.25),
                  rot_intru.animate.set_opacity(0.25), run_time=1.4)
        leg = self.legenda("Atenuada enquanto ainda era 7 kHz, ela nunca chega a se dobrar", leg, COR_OK)
        self.wait(0.6)

        # --- a banda de transição e as duas saídas ----------------------------
        self.play(FadeOut(intru), FadeOut(rot_intru), run_time=0.5)
        self.trocar_titulo(titulo, "5 · O filtro ideal não existe")
        transicao = Polygon(axf.c2p(4, 0), axf.c2p(5, 0), axf.c2p(5, 1.1), axf.c2p(4, 1.1),
                            stroke_width=0).set_fill(COR_FILTRO, opacity=0.3)
        rot_trans = txt("banda de transição", 18, COR_FILTRO).next_to(axf.c2p(4.5, 1.1), UP, buff=0.3)
        leg = self.legenda("Todo filtro real precisa de espaço para descer, entre f_max e f_s/2", leg, COR_FILTRO)
        self.play(FadeIn(transicao), FadeIn(rot_trans))

        opcoes = VGroup(
            caixa("folga de guarda\namostrar um pouco acima de 2·f_max", 5.6, 1.0, COR_AMOSTRA, 18),
            caixa("sobreamostragem\nf_s muito alta, filtro analógico simples,\ncorte fino no FIR digital",
                  5.9, 1.3, COR_DIG, 18),
        ).arrange(RIGHT, buff=0.5).move_to(P(0, -1.75))
        leg = self.legenda("Daí as duas saídas de projeto", leg)
        self.play(FadeIn(opcoes[0], shift=UP * 0.2))
        self.play(FadeIn(opcoes[1], shift=UP * 0.2))
        leg = self.legenda("O LLRF usa a segunda: ADC rápido e o trabalho fino dentro da FPGA", leg, COR_DIG)
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 6
    def cena_quantizacao(self):
        """O segundo erro: independente do primeiro, e previsível."""
        self.titulo_cena("6 · Quantização: o segundo erro")

        bits = ValueTracker(2)
        fundo = 1.2
        xs = np.linspace(0, 2, 400)
        sinal = lambda t: 1.05 * np.sin(TAU * t / 2)

        ax = eixos(P(-3.3, 1.25), 6.6, 2.2, [0, 2, 0.5], [-fundo, fundo, 0.5])
        ax_e = eixos(P(-3.3, -1.45), 6.6, 1.1, [0, 2, 0.5], [-0.35, 0.35, 0.25])
        r_e = txt("erro de quantização", 17, COR_DIG)
        rotulo_eixo(ax_e, r_e, 0.1)
        onda = curva(ax, sinal, COR_SINAL, 3)

        def niveis():
            b = int(round(bits.get_value()))
            passo = 2 * fundo / 2 ** b
            return VGroup(*[Line(ax.c2p(0, v), ax.c2p(2, v), color=GREY_D, stroke_width=1)
                            for v in np.arange(-fundo, fundo, passo)])

        def degraus():
            b = int(round(bits.get_value()))
            px, py = escada(list(xs), list(quantizar(sinal(xs), b, fundo)))
            return polilinha(ax, px, py, COR_DIG, 3)

        def erro():
            b = int(round(bits.get_value()))
            e = quantizar(sinal(xs), b, fundo) - sinal(xs)
            return polilinha(ax_e, xs, e, COR_DIG, 2)

        g_niveis = always_redraw(niveis)
        g_degraus = always_redraw(degraus)
        g_erro = always_redraw(erro)
        rot_bits = always_redraw(lambda: tex(rf"B = {int(round(bits.get_value()))}\ \text{{bits}}",
                                             COR_DIG, 30).move_to(P(-3.3, 2.65)))

        contas = VGroup(
            tex(r"\Delta = \frac{V_{FS}}{2^B}", WHITE, 34),
            tex(r"\sigma_q^2 = \frac{\Delta^2}{12}", WHITE, 34),
            tex(r"SQNR \approx 6{,}02\,B + 1{,}76\ \text{dB}", COR_DIG, 32),
        ).arrange(DOWN, buff=0.4).move_to(P(3.7, 1.55))
        cada_bit = txt("cada bit vale ≈ 6 dB", 24, COR_DIG).next_to(contas, DOWN, buff=0.35)

        leg = self.legenda("A amostragem decide quando medir; a quantização, com quantos bits")
        self.play(Create(ax), Create(ax_e), FadeIn(r_e))
        self.play(Create(onda), run_time=1.2)
        self.add(g_niveis, g_degraus, g_erro, rot_bits)
        leg = self.legenda("Cada amostra é arredondada para o nível mais próximo", leg)
        self.wait(0.6)
        for b in (3, 4, 6):
            self.play(bits.animate.set_value(b), run_time=1.1)
            self.wait(0.5)
        leg = self.legenda("Mais bits, degraus menores, erro menor — e a conta é fechada", leg)
        self.play(Write(contas[0]), run_time=1.0)
        self.play(Write(contas[1]), run_time=1.0)
        self.play(Write(contas[2]), run_time=1.3)
        self.play(FadeIn(cada_bit, shift=UP * 0.2))
        self.wait(0.8)

        self.play(FadeOut(VGroup(contas, cada_bit)))
        tabela = VGroup(
            txt("B", 22, COR_EIXO), txt("SQNR", 22, COR_EIXO), txt("uso típico", 22, COR_EIXO),
            txt("8", 22, WHITE), txt("49,9 dB", 22, WHITE), txt("aquisição grosseira", 20, GREY_A),
            txt("12", 22, WHITE), txt("74,0 dB", 22, WHITE), txt("ADCs rápidos gerais", 20, GREY_A),
            txt("14", 22, COR_DIG), txt("86,0 dB", 22, COR_DIG), txt("ADCs de LLRF", 20, COR_DIG),
            txt("16", 22, WHITE), txt("98,1 dB", 22, WHITE), txt("medida de precisão", 20, GREY_A),
        ).arrange_in_grid(rows=5, cols=3, buff=(0.45, 0.3)).move_to(P(3.6, 1.35))
        leg = self.legenda("Os ADCs de LLRF ficam em 14 bits: 86 dB de faixa dinâmica", leg, COR_DIG)
        self.play(FadeIn(tabela, shift=UP * 0.2), run_time=1.2)
        self.wait(0.8)

        ressalvas = txt("duas ressalvas: a conta supõe o sinal ocupando a faixa inteira — 20 dB abaixo\n"
                        "do fundo de escala custa 20 dB de SQNR; e o ruído se espalha por [0, f_s/2],\n"
                        "então sobreamostrar e filtrar ganha 3 dB por cada duplicação de f_s",
                        20, GREY_B, line_spacing=0.9).move_to(P(0.3, -2.45))
        self.play(FadeOut(VGroup(ax, ax_e, r_e, onda, g_niveis, g_degraus, g_erro, rot_bits)),
                  tabela.animate.move_to(P(0, 1.3)))
        self.play(FadeIn(ressalvas, shift=UP * 0.2))
        leg = self.legenda("E é por isso que existe controle de ganho antes do ADC", leg)
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 7
    def cena_reconstrucao(self):
        """Voltar ao contínuo: o ideal e o que o DAC realmente faz."""
        titulo = self.titulo_cena("7 · Reconstrução: da sequência de volta à onda")

        T = 0.1
        ts = np.arange(0, 1.001, T)
        sinal = lambda t: np.cos(TAU * t) * 0.9
        ax = eixos(P(0, 0.9), 12.2, 2.6, [0, 1, 0.1], [-1.25, 1.25, 1])
        r_t = txt("tempo [ms]  →", 18, COR_EIXO).next_to(ax, DOWN, buff=0.4).align_to(ax, RIGHT)
        amostras = VGroup(*[haste(ax, t, sinal(t), COR_AMOSTRA, 0.08) for t in ts])

        leg = self.legenda("O teorema promete reconstrução exata. A fórmula dessa promessa é a sinc")
        self.play(Create(ax), FadeIn(r_t))
        self.play(LaggedStart(*[FadeIn(a) for a in amostras], lag_ratio=0.08), run_time=1.5)

        xs = np.linspace(0, 1, 500)
        sinc_de = lambda t: polilinha(ax, xs, sinal(t) * np.sinc((xs - t) / T), COR_SINAL, 3)
        formula = tex(r"x(t) = \sum_n x[n]\,\mathrm{sinc}\!\left(\frac{t - nT}{T}\right)", WHITE, 34
                      ).move_to(P(-3.6, -1.85))

        uma = sinc_de(0.5)
        self.play(Create(uma), run_time=1.4)
        leg = self.legenda("Uma sinc por amostra, escalada pelo valor dela — esta é a da amostra "
                           "em t = 0,5", leg)
        outras = VGroup(*[sinc_de(t) for t in ts if abs(t - 0.5) > 1e-9])
        for s in outras:
            s.set_stroke(COR_SINAL, 1.2, opacity=0.35)
        self.play(uma.animate.set_stroke(COR_SINAL, 1.2, opacity=0.35),
                  LaggedStart(*[Create(s) for s in outras], lag_ratio=0.1), run_time=2.2)
        sincs = VGroup(uma, outras)
        self.play(Write(formula), run_time=1.3)
        leg = self.legenda("Cada amostra contribui com a sua, e elas se cancelam nas outras amostras", leg)

        # a curva verde é a soma de verdade (inclui amostras fora da janela visível,
        # porque a interpolação ideal precisa de todas elas)
        ks = np.arange(-25, 36)
        rec = sum(sinal(k * T) * np.sinc((xs - k * T) / T) for k in ks)
        soma = polilinha(ax, xs, rec, COR_OK, 4)
        self.play(Create(soma), run_time=1.6)
        porque = txt("a soma devolve o sinal porque a sinc é,\n"
                     "na frequência, um passa-baixa ideal em f_s/2:\n"
                     "reconstruir é apagar todas as réplicas",
                     20, GREY_B, line_spacing=0.9).move_to(P(3.9, -1.85))
        self.play(FadeIn(porque, shift=UP * 0.2))
        leg = self.legenda("Mas a sinc é infinita nos dois sentidos: o interpolador ideal não é causal", leg)
        self.wait(0.8)

        # --- o que o DAC faz de verdade ---------------------------------------
        self.play(FadeOut(sincs), FadeOut(formula), FadeOut(porque), FadeOut(soma))
        self.trocar_titulo(titulo, "7 · O que o DAC realmente faz: Zero-Order Hold")
        px, py = escada(list(ts), [sinal(t) for t in ts])
        zoh = polilinha(ax, px, py, COR_DIG, 3)
        orig = polilinha(ax, xs, sinal(xs), GREY_D, 2)
        leg = self.legenda("Ele segura cada valor até a amostra seguinte: uma escada", leg, COR_DIG)
        self.play(Create(orig), Create(zoh), run_time=1.8)
        self.wait(0.8)

        self.play(FadeOut(VGroup(ax, r_t, amostras, zoh, orig)))
        axf = eixos(P(0, 0.55), 12.0, 2.3, [0, 3, 0.5], [0, 1.15, 1])
        r_f = txt("frequência, em múltiplos de f_s  →", 18, COR_EIXO
                  ).next_to(axf, DOWN, buff=0.45).align_to(axf, RIGHT)
        mx = marcar_x(axf, [0, 0.5, 1, 2, 3], ["0", "f_s/2", "f_s", "2f_s", "3f_s"], 17, 0.14)
        u = np.linspace(0.0005, 3, 600)
        resp = polilinha(axf, u, np.abs(np.sinc(u)), COR_DIG, 3)
        rot_resp = tex(r"|H_{ZOH}(f)| = \left|\frac{\sin(\pi f/f_s)}{\pi f/f_s}\right|",
                       COR_DIG, 30).move_to(P(3.6, 2.2))

        marca = Dot(axf.c2p(0.5, 2 / np.pi), radius=0.08, color=COR_ALIAS)
        rot_droop = VGroup(tex(r"2/\pi = 0{,}637", COR_ALIAS, 26),
                           txt("−3,9 dB em f_s/2", 21, COR_ALIAS)
                           ).arrange(DOWN, buff=0.18).move_to(P(-3.3, 1.85))
        guia = tracejada(axf.c2p(0.5, 0), axf.c2p(0.5, 2 / np.pi), COR_ALIAS, 2, 0.08)

        leg = self.legenda("A escada tem resposta em frequência — e ela não é plana", leg)
        self.play(Create(axf), FadeIn(mx), FadeIn(r_f))
        self.play(Create(resp), FadeIn(rot_resp), run_time=1.6)
        self.play(Create(guia), FadeIn(marca), FadeIn(rot_droop))
        leg = self.legenda("Defeito 1 — droop: a resposta cai dentro da própria banda útil", leg, COR_ALIAS)
        self.wait(0.6)

        imagens = VGroup(*[banda(axf, f, 0.09, float(np.abs(np.sinc(f))), COR_ALIAS, 0.55)
                           for f in (0.9, 1.1, 1.9, 2.1)])
        rot_img = txt("imagens: a escada atenua as réplicas, mas não as elimina",
                      20, COR_ALIAS).move_to(P(0.9, -1.95))
        suave = caixa("filtro de suavização\nanalógico, na saída do DAC", 5.0, 0.95, COR_FILTRO, 18
                      ).move_to(P(-3.3, -2.15))
        corrige = caixa("correção do droop\nno digital, antes do DAC", 4.6, 0.95, COR_DIG, 18
                        ).move_to(P(2.6, -2.15))

        leg = self.legenda("Defeito 2 — imagens em torno de f_s, 2f_s, …", leg, COR_ALIAS)
        self.play(LaggedStart(*[DrawBorderThenFill(i) for i in imagens], lag_ratio=0.2), run_time=1.4)
        self.play(FadeIn(rot_img, shift=UP * 0.2))
        leg = self.legenda("Cada defeito tem o seu remédio, e é essa a cadeia do lado do DAC", leg)
        self.play(FadeOut(rot_img), FadeIn(suave, shift=UP * 0.2), FadeIn(corrige, shift=UP * 0.2))
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 8
    def cena_subamostragem(self):
        """Quando o aliasing deixa de ser defeito e passa a ser ferramenta."""
        titulo = self.titulo_cena("8 · Sub-amostragem deliberada")

        comp = VGroup(
            txt("critério", 22, COR_EIXO), txt("taxa exigida", 22, COR_EIXO),
            txt("Nyquist sobre f_max = 501 MHz", 22, COR_ALIAS), txt("> 1000 MSps", 22, COR_ALIAS),
            txt("Nyquist sobre a largura de banda = 2 MHz", 22, COR_OK), txt("> 4 MSps", 22, COR_OK),
        ).arrange_in_grid(rows=3, cols=2, buff=(0.7, 0.32)).move_to(P(0, 1.5))
        contexto = txt("uma banda de 2 MHz em torno de uma portadora de 500 MHz", 23, GREY_A
                       ).next_to(comp, UP, buff=0.45)

        leg = self.legenda("O critério de Nyquist fala de f_max porque supõe o sinal ocupando tudo")
        self.play(FadeIn(contexto, shift=UP * 0.2))
        self.play(FadeIn(comp[0]), FadeIn(comp[1]))
        self.play(FadeIn(comp[2], shift=RIGHT * 0.2), FadeIn(comp[3], shift=RIGHT * 0.2))
        leg = self.legenda("Mas num sinal de RF a informação está na largura de banda, não na portadora", leg)
        self.play(FadeIn(comp[4], shift=RIGHT * 0.2), FadeIn(comp[5], shift=RIGHT * 0.2))
        duas_ordens = txt("duas ordens de grandeza de diferença — por isso ninguém amostra RF direto",
                          22, GREY_B).move_to(P(0, -0.5))
        self.play(FadeIn(duas_ordens, shift=UP * 0.2))
        leg = self.legenda("Então amostra-se de propósito abaixo de 2·f_max, e deixa-se a banda dobrar", leg)
        self.wait(0.6)
        self.play(FadeOut(VGroup(contexto, comp, duas_ordens)))

        # --- a conta, no eixo de frequência -----------------------------------
        self.trocar_titulo(titulo, "8 · A portadora de 500 MHz amostrada a 80 MSps")
        axf = eixos(P(0, 0.9), 12.2, 1.9, [0, 560, 40], [0, 1.1, 1])
        r_f = txt("frequência [MHz]  →", 18, COR_EIXO).next_to(axf, DOWN, buff=0.5).align_to(axf, RIGHT)
        mx = marcar_x(axf, [0, 40, 480, 520], ["0", "40", "480", "520"], 16, 0.14)
        zonas = VGroup(*[Polygon(axf.c2p(k * 40, 0), axf.c2p((k + 1) * 40, 0),
                                 axf.c2p((k + 1) * 40, 1.05), axf.c2p(k * 40, 1.05),
                                 stroke_width=0).set_fill(GREY_E if k % 2 == 0 else "#1b2430",
                                                          opacity=0.6) for k in range(14)])
        rot_zona1 = txt("1ª zona\n0 a 40 MHz", 17, COR_OK, line_spacing=0.85
                        ).next_to(axf.c2p(20, 1.05), UP, buff=0.14)
        rot_zona13 = txt("13ª zona (ímpar:\nnão inverte o espectro)", 17, GREY_A, line_spacing=0.85
                         ).next_to(axf.c2p(500, 1.05), UP, buff=0.14)
        alvo = banda(axf, 500, 14, 0.9, COR_SINAL, 0.6)

        leg = self.legenda("As zonas de Nyquist têm 40 MHz: a portadora cai na 13ª "
                           "(a banda está exagerada para caber na tela)", leg)
        self.play(FadeIn(zonas), Create(axf), FadeIn(mx), FadeIn(r_f))
        self.play(DrawBorderThenFill(alvo), FadeIn(rot_zona13), run_time=1.2)
        self.play(FadeIn(rot_zona1))

        conta = tex(r"f_{ap} = \big| 500 - 80 \cdot \mathrm{round}(500/80) \big| "
                    r"= |500 - 480| = 20\ \text{MHz}", WHITE, 34).move_to(P(0, -1.25))
        leg = self.legenda("A regra da dobra da cena 4, com os números do assunto 1", leg)
        self.play(Write(conta), run_time=1.8)

        copia = banda(axf, 20, 14, 0.9, COR_OK, 0.6)
        arco = ArcBetweenPoints(axf.c2p(500, 0.95), axf.c2p(20, 0.95), angle=-PI / 3.2,
                                color=COR_OK, stroke_width=3)
        self.play(Create(arco), run_time=1.2)
        self.play(TransformFromCopy(alvo, copia), run_time=1.4)
        leg = self.legenda("Os 500 MHz aparecem em 20 MHz, onde a eletrônica digital funciona", leg, COR_OK)

        fecho = VGroup(
            tex(r"20\ \text{MHz} = f_s/4", COR_OK, 36),
            txt("a IF de 20 MHz do assunto 1 e a regra f_s = 4·f_IF do assunto 7.1\n"
                "são a mesma escolha de projeto, vista de dois lugares",
                21, GREY_B, line_spacing=0.9),
        ).arrange(DOWN, buff=0.3).move_to(P(0, -2.1))
        self.play(FadeOut(conta), FadeIn(fecho, shift=UP * 0.2), run_time=1.2)
        self.wait(1.4)

        # --- o que muda nesse regime ------------------------------------------
        self.play(FadeOut(VGroup(axf, mx, r_f, zonas, alvo, copia, arco, rot_zona1, rot_zona13, fecho)))
        self.trocar_titulo(titulo, "8 · O preço da sub-amostragem")
        precos = VGroup(
            caixa("o anti-aliasing passa a ser passa-banda\ntem de deixar entrar só a zona escolhida —\n"
                  "senão o ruído de todas as outras se dobra para dentro", 8.2, 1.3, COR_FILTRO, 18),
            caixa("a zona importa\nzonas pares invertem o espectro, e isso\ntroca o sinal da fase medida",
                  8.2, 1.3, COR_ALIAS, 18),
            caixa("o jitter do clock passa a dominar\nΔv ≈ (dv/dt)·Δt cresce com a portadora,\n"
                  "não com a frequência aparente", 8.2, 1.3, COR_AMOSTRA, 18),
        ).arrange(DOWN, buff=0.35).move_to(P(0, 0.2))
        leg = self.legenda("Nada é de graça: três coisas mudam de lugar", leg)
        for c in precos:
            self.play(FadeIn(c, shift=UP * 0.2), run_time=0.8)
            self.wait(0.5)
        leg = self.legenda("A última é a conta do assunto 1, cena 5 — e o que impede subir a portadora", leg)
        self.wait(1.2)
        self.limpar()

    # =================================================================== RESUMO
    def cena_resumo(self):
        titulo = Text("Amostragem e Aliasing — resumo", font_size=40, weight=BOLD).move_to(P(0, 3.1))
        itens = VGroup(
            Text("A sequência não identifica a frequência: f e f + k·f_s são indistinguíveis",
                 font_size=25, t2c={"f e f + k·f_s": COR_ALIAS}),
            Text("Amostrar replica o espectro a cada f_s; o critério f_s > 2·f_max impede que se toquem",
                 font_size=25, t2c={"f_s > 2·f_max": COR_OK}),
            Text("Violado o critério, a regra da dobra diz onde cada frequência vai cair",
                 font_size=25, t2c={"regra da dobra": COR_ALIAS}),
            Text("A defesa é um filtro analógico antes do ADC — depois dele não há remédio",
                 font_size=25, t2c={"filtro analógico": COR_FILTRO}),
            Text("A quantização é o outro erro, independente: cada bit vale ≈ 6 dB de SQNR",
                 font_size=25, t2c={"cada bit vale ≈ 6 dB": COR_DIG}),
            Text("Reconstruir é apagar as réplicas: a sinc ideal, o ZOH real e o seu droop de −3,9 dB",
                 font_size=25, t2c={"ZOH": COR_DIG, "−3,9 dB": COR_ALIAS}),
            Text("Em RF, amostra-se abaixo de 2·f_max de propósito: o que conta é a largura de banda",
                 font_size=25, t2c={"largura de banda": COR_OK}),
        ).arrange(DOWN, buff=0.42, aligned_edge=LEFT)
        for it in itens:
            ajustar(it, 13.0)
        itens.move_to(P(0, 0.15))

        self.play(Write(titulo), run_time=1.2)
        for it in itens:
            self.play(FadeIn(it, shift=RIGHT * 0.25), run_time=0.6)
            self.wait(0.45)
        self.wait(1.0)

        ponte = txt("o próximo assunto — 4, Filtros — usa tudo isto: um filtro só faz sentido\n"
                    "quando se sabe o que é a frequência de Nyquist do sistema",
                    22, GREY_B, line_spacing=0.9).move_to(P(0, -2.95))
        self.play(FadeIn(ponte, shift=UP * 0.2))
        self.wait(2.0)
        self.play(FadeOut(VGroup(titulo, itens, ponte)), run_time=1.2)
        self.wait(0.5)
