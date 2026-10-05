# -*- coding: utf-8 -*-
"""
Filtro FIR: média ponderada das últimas N amostras
==================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/Detecção de amplitude e fase em RF/Digital Down Conversion/filtro_fir.py" FiltroFIR   # rascunho
    manim -pqh "src/Detecção de amplitude e fase em RF/Digital Down Conversion/filtro_fir.py" FiltroFIR   # final

Requer LaTeX (MathTex).

Roteiro (segue "docs/Detecção de amplitude e fase em RF/Digital Down Conversion/Filtro FIR"):
    Abertura
    Cena 1 - A equação: y[n] = Σ h[k]·x[n−k], N taps, ordem N − 1
    Cena 2 - A estrutura: linha de atrasos, multiplicadores e somadores (clock a clock)
    Cena 3 - Resposta ao impulso finita × infinita (sem e com realimentação)
    Cena 4 - Na prática: média móvel sobre um sinal ruidoso; N maior = mais suave e mais atraso
    Cena 5 - Fase linear: o FIR só atrasa; o IIR deforma
    Cena 6 - O custo: corte abrupto exige muitos taps
    Cena 7 - FIR × IIR
    Resumo
"""

import numpy as np
from manim import *

# Paleta didática (fixa em todas as cenas)
COR_X = BLUE             # entrada / amostras
COR_H = GOLD             # coeficientes h[k]
COR_Y = GREEN            # saída y[n]
COR_ATRASO = TEAL        # registradores de atraso
COR_IIR = ORANGE         # filtro IIR (comparação)
COR_RUIDO = RED
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}
H_EXEMPLO = [0.1, 0.4, 0.4, 0.1]          # coeficientes da cena da estrutura
X_EXEMPLO = [2, 5, 1, 4, 3]               # entrada da cena da estrutura


# =============================================================================
# Utilitários de construção
# =============================================================================
def P(x, y):
    return np.array([x, y, 0.0])


def tex(s, cor=WHITE, tamanho=34):
    return MathTex(s, color=cor, font_size=tamanho)


def tex_partes(partes, tamanho=34):
    """Fórmula multicolorida. partes = [(tex, cor), ...]."""
    m = MathTex(*[p[0] for p in partes], font_size=tamanho)
    for sub, p in zip(m, partes):
        sub.set_color(p[1])
    return m


def fio(pontos, cor=WHITE, largura=3):
    g = VGroup(*[Line(pontos[k], pontos[k + 1], color=cor, stroke_width=largura) for k in range(len(pontos) - 2)])
    g.add(Arrow(pontos[-2], pontos[-1], buff=0, color=cor, stroke_width=largura,
                max_tip_length_to_length_ratio=0.25, max_stroke_width_to_length_ratio=10))
    return g


def caixa_tex(rotulo, largura=0.9, altura=0.65, cor=WHITE, tamanho=28):
    r = RoundedRectangle(corner_radius=0.08, width=largura, height=altura, color=cor, stroke_width=3)
    return VGroup(r, tex(rotulo, cor, tamanho).move_to(r))


def somador(cor=WHITE, raio=0.25):
    c = Circle(radius=raio, color=cor, stroke_width=3)
    return VGroup(c, tex("+", cor, 30).move_to(c))


def ganho(cor=COR_H):
    """Triângulo de multiplicador apontando para baixo."""
    return Triangle(color=cor, stroke_width=3).rotate(PI).scale(0.3)


def eixos_tempo(centro, largura, altura, x_range, y_range):
    return Axes(x_range=x_range, y_range=y_range, x_length=largura, y_length=altura,
                axis_config=EIXO_CFG).move_to(centro)


def rotulo_eixo(ax, mob):
    """Coloca um rótulo acima do canto esquerdo de um eixo."""
    return mob.next_to(ax, UP, buff=0.04).align_to(ax, LEFT)


def haste(ax, x, y, cor, raio=0.06, largura=2):
    return VGroup(Line(ax.c2p(x, 0), ax.c2p(x, y), color=cor, stroke_width=largura),
                  Dot(ax.c2p(x, y), radius=raio, color=cor))


def polilinha(ax, xs, ys, cor, largura=3):
    return VMobject().set_points_as_corners([ax.c2p(a, b) for a, b in zip(xs, ys)]).set_stroke(cor, largura)


def fir_causal(x, h):
    return np.array([sum(h[k] * x[n - k] for k in range(len(h)) if n - k >= 0) for n in range(len(x))])


def iir_1a_ordem(x, a):
    y = np.zeros(len(x))
    for n in range(len(x)):
        y[n] = a * (y[n - 1] if n else 0) + (1 - a) * x[n]
    return y


def passa_baixa_janelado(N, fc=0.15):
    """FIR passa-baixa por janela de Hamming (sinc truncado), fc em ciclos/amostra."""
    n = np.arange(N) - (N - 1) / 2
    h = 2 * fc * np.sinc(2 * fc * n) * np.hamming(N)
    return h / h.sum()


def resposta_db(h, f):
    k = np.arange(len(h))
    H = np.abs(np.exp(-2j * np.pi * np.outer(f, k)) @ h)
    return 20 * np.log10(np.maximum(H, 1e-6))


# =============================================================================
# Cena
# =============================================================================
class FiltroFIR(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_equacao()
        self.cena_estrutura()
        self.cena_impulso()
        self.cena_media()
        self.cena_fase()
        self.cena_custo()
        self.cena_fir_iir()
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
        titulo = Text("Filtro FIR", font_size=64, weight=BOLD)
        sub = Text("Finite Impulse Response: uma média ponderada das últimas N amostras", font_size=28,
                   color=GREY_A)
        eq = tex(r"y[n] = \sum_{k=0}^{N-1} h[k]\,x[n-k]", COR_Y, 40)
        g = VGroup(titulo, sub, eq).arrange(DOWN, buff=0.4)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(eq, shift=UP * 0.2))
        self.wait(1.2)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_equacao(self):
        self.titulo_cena("1 · A equação")
        eq = tex_partes([(r"y[n]", COR_Y), (r" = \sum_{k=0}^{N-1}", WHITE), (r"h[k]", COR_H), (r"\cdot", WHITE),
                         (r"x[n-k]", COR_X)], 44).move_to(P(0, 2.0))
        defs = VGroup(
            VGroup(tex(r"y[n]", COR_Y, 30), Text("saída no instante n", font_size=22)).arrange(RIGHT, buff=0.3),
            VGroup(tex(r"x[n],\ x[n-k]", COR_X, 30), Text("entrada atual e amostras passadas", font_size=22)
                   ).arrange(RIGHT, buff=0.3),
            VGroup(tex(r"h[k]", COR_H, 30), Text("coeficientes: definem o comportamento (ex.: o corte)",
                                                 font_size=22)).arrange(RIGHT, buff=0.3),
            VGroup(tex(r"N", WHITE, 30), Text("número de coeficientes (taps); ordem do filtro = N − 1",
                                              font_size=22)).arrange(RIGHT, buff=0.3),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to(P(0, 0.0))
        exp = tex_partes([(r"N = 4:\quad y[n] = ", WHITE), (r"h_0", COR_H), (r"x[n]", COR_X), (r" + ", WHITE),
                          (r"h_1", COR_H), (r"x[n-1]", COR_X), (r" + ", WHITE), (r"h_2", COR_H), (r"x[n-2]", COR_X),
                          (r" + ", WHITE), (r"h_3", COR_H), (r"x[n-3]", COR_X)], 34).move_to(P(0, -2.0))

        leg = self.legenda("Pegar a amostra atual e as anteriores, pesar cada uma e somar tudo")
        self.play(Write(eq), run_time=2)
        self.play(LaggedStart(*[FadeIn(d, shift=RIGHT * 0.2) for d in defs], lag_ratio=0.3), run_time=2.5)
        leg = self.legenda("Por exemplo, com 4 coeficientes:", leg)
        self.play(Write(exp), run_time=2)
        leg = self.legenda("Só entradas: nenhuma saída passada entra na conta (não há realimentação)", leg, COR_Y)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 2
    def cena_estrutura(self):
        self.titulo_cena("2 · Linha de atrasos, multiplicadores e somadores")
        h = H_EXEMPLO
        tx = [-4.8, -2.2, 0.4, 3.0]
        yt, yg, ys = 1.75, 0.55, -0.7
        x_in = tex(r"x[n]", COR_X, 30).move_to(P(-6.3, yt))
        regs = VGroup(*[caixa_tex(r"T", 0.8, 0.6, COR_ATRASO, 28).move_to(P((tx[k] + tx[k + 1]) / 2, yt))
                        for k in range(3)])
        nos = VGroup(*[Dot(P(x, yt), radius=0.06) for x in tx])
        linha_topo = VGroup(fio([x_in.get_right() + RIGHT * 0.1, P(tx[0], yt)]),
                            *[fio([P(tx[k], yt), regs[k].get_left()]) for k in range(3)],
                            *[Line(regs[k].get_right(), P(tx[k + 1], yt), stroke_width=3) for k in range(3)])
        tris = VGroup(*[ganho().move_to(P(x, yg)) for x in tx])
        r_h = VGroup(*[tex(rf"h_{k} = {v}", COR_H, 24).next_to(tris[k], LEFT, buff=0.15) for k, v in enumerate(h)])
        desce = VGroup(*[fio([P(x, yt), tris[k].get_top()], GREY_A, 2) for k, x in enumerate(tx)])
        somas = VGroup(*[somador().move_to(P(x, ys)) for x in tx[1:]])
        liga = VGroup(fio([tris[0].get_bottom(), P(tx[0], ys), somas[0].get_left()], GREY_A, 2),
                      *[fio([tris[k].get_bottom(), somas[k - 1].get_top()], GREY_A, 2) for k in range(1, 4)],
                      *[fio([somas[k].get_right(), somas[k + 1].get_left()], GREY_A, 2) for k in range(2)])
        y_out = tex(r"y[n]", COR_Y, 30).move_to(P(5.4, ys))
        f_out = fio([somas[2].get_right(), y_out.get_left() + LEFT * 0.1], COR_Y)

        leg = self.legenda("Registradores de atraso (z⁻¹) guardam as amostras passadas")
        self.play(FadeIn(x_in), Create(linha_topo), FadeIn(regs), FadeIn(nos), run_time=1.5)
        leg = self.legenda("Cada derivação é multiplicada pelo seu coeficiente h[k]", leg, COR_H)
        self.play(Create(desce), FadeIn(tris), FadeIn(r_h))
        leg = self.legenda("Um somador final junta todos os produtos: o sinal só flui para a frente", leg, COR_Y)
        self.play(Create(liga), FadeIn(somas), Create(f_out), FadeIn(y_out), run_time=1.5)

        def bolinha(v, k):
            c = Circle(radius=0.27, color=COR_X, stroke_width=3, fill_color=FUNDO, fill_opacity=1)
            return VGroup(c, Text(f"{v:g}", font_size=22, color=COR_X).move_to(c)).move_to(P(tx[k], yt + 0.6))

        def produtos(vals):
            return VGroup(*[Text(f"{h[k] * vals[k]:.1f}", font_size=18, color=COR_H).next_to(tris[k], RIGHT, buff=0.1)
                            for k in range(4)])

        def saida(vals, s):
            yv = sum(h[k] * vals[k] for k in range(4))
            termos = " + ".join(rf"{h[k]}\cdot{vals[k]}" for k in range(4))
            eq = tex(rf"y[{s}] = {termos} = {yv:.1f}", COR_Y, 30).move_to(P(0, -1.75))
            val = Text(f"= {yv:.1f}", font_size=24, color=COR_Y).next_to(y_out, DOWN, buff=0.15)
            return VGroup(eq, val)

        vals = [0, 0, 0, 0]
        bolas = [bolinha(0, k) for k in range(4)]
        prods = produtos(vals)
        out = saida(vals, -1)
        rot_regs = Text("registradores começam zerados", font_size=18, color=GREY_A).move_to(P(0.4, yt + 1.15))
        self.play(*[FadeIn(b) for b in bolas], FadeIn(rot_regs))
        leg = self.legenda("A cada clock as amostras andam uma casa e um novo y[n] é calculado", leg)
        self.play(FadeOut(rot_regs))
        for s, nova in enumerate(X_EXEMPLO):
            nova_bola = bolinha(nova, 0)
            self.play(*[bolas[k].animate.move_to(P(tx[k + 1], yt + 0.6)) for k in range(3)],
                      FadeOut(bolas[3], shift=RIGHT * 0.4), FadeIn(nova_bola, shift=RIGHT * 0.4),
                      *[Indicate(r, color=WHITE, scale_factor=1.15) for r in regs], run_time=0.8)
            bolas = [nova_bola] + bolas[:3]
            vals = [nova] + vals[:3]
            novos_prods = produtos(vals)
            nova_saida = saida(vals, s)
            if s == 0:
                self.play(FadeIn(novos_prods), FadeIn(nova_saida), run_time=0.8)
            else:
                self.play(ReplacementTransform(prods, novos_prods), ReplacementTransform(out, nova_saida), run_time=0.8)
            prods, out = novos_prods, nova_saida
            self.wait(0.5 if s > 1 else 1.0)
        leg = self.legenda("Em Verilog/VHDL: shift register + blocos MAC trabalhando em paralelo", leg, COR_ATRASO)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 3
    def cena_impulso(self):
        self.titulo_cena("3 · Resposta ao impulso: finita")
        nmax = 16
        imp = np.zeros(nmax)
        imp[1] = 1
        h = np.array(H_EXEMPLO)
        y_fir = fir_causal(imp, h)
        y_iir = iir_1a_ordem(imp, 0.75)
        cfg = dict(largura=5.8, altura=2.2, x_range=[0, nmax, 2], y_range=[0, 1.1, 0.5])
        ax_in = eixos_tempo(P(-3.5, 1.2), **cfg)
        ax_fir = eixos_tempo(P(-3.5, -1.75), **cfg)
        ax_iir = eixos_tempo(P(3.5, -1.75), **cfg)
        r_in = rotulo_eixo(ax_in, Text("entrada: um único pulso (impulso)", font_size=18, color=COR_X))
        r_fir = rotulo_eixo(ax_fir, Text("saída do FIR: os próprios h[k], depois zero", font_size=18, color=COR_Y))
        r_iir = rotulo_eixo(ax_iir, Text("saída de um IIR: decai, mas nunca zera", font_size=18, color=COR_IIR))
        h_in = VGroup(*[haste(ax_in, n, imp[n], COR_X, 0.06, 3) for n in range(nmax)])
        h_fir = VGroup(*[haste(ax_fir, n, y_fir[n], COR_Y, 0.06, 3) for n in range(nmax)])
        h_iir = VGroup(*[haste(ax_iir, n, y_iir[n] * 3, COR_IIR, 0.06, 3) for n in range(nmax)])
        chave = BraceBetweenPoints(ax_fir.c2p(0.7, 0.75), ax_fir.c2p(4.3, 0.75), UP, color=COR_Y)
        r_chave = Text("N = 4 amostras", font_size=16, color=COR_Y).next_to(chave, UP, buff=0.05)
        eq_iir = tex(r"y[n] = a\,y[n-1] + (1-a)\,x[n]", COR_IIR, 26).next_to(ax_iir, UP, buff=0.45)

        leg = self.legenda("Aplicamos um único pulso na entrada")
        self.play(Create(ax_in), FadeIn(r_in), LaggedStart(*[GrowFromPoint(h, h[0].get_start()) for h in h_in],
                                                            lag_ratio=0.05))
        leg = self.legenda("O FIR responde com os seus coeficientes e zera depois de N amostras: resposta finita",
                           leg, COR_Y)
        self.play(Create(ax_fir), FadeIn(r_fir))
        self.play(LaggedStart(*[GrowFromPoint(h, h[0].get_start()) for h in h_fir], lag_ratio=0.1), run_time=2)
        self.play(GrowFromCenter(chave), FadeIn(r_chave))
        leg = self.legenda("Com realimentação (IIR), a saída volta para a conta e a resposta nunca acaba", leg,
                           COR_IIR)
        self.play(Create(ax_iir), FadeIn(r_iir), Write(eq_iir))
        self.play(LaggedStart(*[GrowFromPoint(h, h[0].get_start()) for h in h_iir], lag_ratio=0.1), run_time=2)
        leg = self.legenda("Sem realimentação, o FIR nunca fica instável", leg, COR_Y)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 4
    def cena_media(self):
        self.titulo_cena("4 · Na prática: suavizar um sinal ruidoso")
        rng = np.random.default_rng(8)
        nmax = 100
        n = np.arange(nmax)
        limpo = np.sin(TAU * n / 45)
        x = limpo + 0.65 * rng.uniform(-1, 1, nmax) * 1.2
        Nv = ValueTracker(1)

        def nn():
            return int(round(Nv.get_value()))

        ax = eixos_tempo(P(-0.2, 0.0), 12.5, 4.0, [0, 100, 10], [-2, 2, 0.5])
        r_ax = rotulo_eixo(ax, Text("entrada ruidosa (cinza) e saída do FIR com coeficientes iguais 1/N (verde)",
                                    font_size=18, color=GREY_A))
        c_x = polilinha(ax, n, x, GREY_B, 2)
        c_y = always_redraw(lambda: polilinha(ax, n, fir_causal(x, np.ones(nn()) / nn()), COR_Y, 5))
        painel = always_redraw(lambda: VGroup(
            Text(f"número de taps N = {nn()}", font_size=24, color=COR_H),
            Text(f"atraso introduzido = (N − 1)/2 = {(nn() - 1) / 2:.1f} amostras", font_size=22, color=COR_ATRASO),
        ).arrange(RIGHT, buff=0.8).move_to(P(0, -2.6)))

        leg = self.legenda("Ex.: acelerômetro de um drone, com a vibração do motor somada à inclinação real")
        self.play(Create(ax), FadeIn(r_ax))
        self.play(Create(c_x), run_time=2)
        self.add(c_y)
        self.play(FadeIn(painel))
        leg = self.legenda("A cada clock, a média ponderada das últimas N amostras vira o novo ponto da saída", leg,
                           COR_Y)
        for v in (5, 10):
            self.play(Nv.animate.set_value(v), run_time=1.5)
            self.wait(0.8)
        leg = self.legenda("Os picos rápidos se diluem na média; sobra a variação lenta que interessa", leg, COR_Y)
        self.wait(1)
        leg = self.legenda("Mais taps: mais suave, porém mais atrasado", leg, COR_ATRASO)
        self.play(Nv.animate.set_value(20), run_time=1.5)
        self.wait(1)
        self.play(Nv.animate.set_value(10), run_time=1.2)
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 5
    def cena_fase(self):
        self.titulo_cena("5 · Fase linear: o FIR só atrasa")
        nmax = 60
        n = np.arange(nmax)
        x = np.where((n >= 12) & (n < 30), 1.0, 0.0)
        Nf = 9
        y_fir = fir_causal(x, np.ones(Nf) / Nf)
        y_iir = iir_1a_ordem(x, 0.8)
        cfg = dict(largura=6.0, altura=3.0, x_range=[0, 60, 10], y_range=[-0.1, 1.2, 0.5])
        ax_f = eixos_tempo(P(-3.5, -0.3), **cfg)
        ax_i = eixos_tempo(P(3.5, -0.3), **cfg)
        cab_f = Text("FIR (simétrico, 9 taps)", font_size=22, color=COR_Y, weight=BOLD).next_to(ax_f, UP, buff=0.25)
        cab_i = Text("IIR de 1ª ordem", font_size=22, color=COR_IIR, weight=BOLD).next_to(ax_i, UP, buff=0.25)
        ent = VGroup(polilinha(ax_f, n, x, COR_X, 3), polilinha(ax_i, n, x, COR_X, 3))
        atrasado = DashedVMobject(polilinha(ax_f, n + (Nf - 1) / 2, x, GREY_A, 2), num_dashes=60)
        s_fir = polilinha(ax_f, n, y_fir, COR_Y, 5)
        s_iir = polilinha(ax_i, n, y_iir, COR_IIR, 5)
        centro = (12 + 29) / 2 + (Nf - 1) / 2
        eixo_sim = DashedLine(ax_f.c2p(centro, -0.1), ax_f.c2p(centro, 1.15), color=YELLOW, stroke_width=2)
        n_f = Text("subida e descida iguais:\nsimétrico em torno do centro atrasado", font_size=16, color=COR_Y
                   ).next_to(ax_f, DOWN, buff=0.2)
        n_i = Text("sobe de um jeito e desce de outro:\na forma foi deformada", font_size=16, color=COR_IIR
                   ).next_to(ax_i, DOWN, buff=0.2)

        leg = self.legenda("Entrada: um pulso retangular (azul)")
        self.play(FadeIn(cab_f), FadeIn(cab_i), Create(ax_f), Create(ax_i))
        self.play(Create(ent), run_time=1.5)
        leg = self.legenda("FIR com coeficientes simétricos: todas as frequências atrasam o mesmo tempo", leg, COR_Y)
        self.play(Create(s_fir), run_time=2)
        self.play(Create(atrasado), Create(eixo_sim), FadeIn(n_f))
        leg = self.legenda("IIR: frequências diferentes atrasam tempos diferentes", leg, COR_IIR)
        self.play(Create(s_iir), run_time=2)
        self.play(FadeIn(n_i))
        leg = self.legenda("Fase linear preserva a forma do sinal: crucial em comunicações e áudio", leg, COR_Y)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 6
    def cena_custo(self):
        self.titulo_cena("6 · O custo: corte abrupto exige muitos taps")
        f = np.linspace(0, 0.5, 600)
        ax = Axes(x_range=[0, 0.5, 0.1], y_range=[-90, 5, 30], x_length=9.4, y_length=4.2,
                  axis_config=EIXO_CFG).move_to(P(-1.4, -0.3))
        marcas = VGroup(*[Text(t, font_size=16, color=COR_EIXO).next_to(ax.c2p(v, -90), DOWN, buff=0.1)
                          for v, t in [(0, "0"), (0.15, "corte"), (0.25, "f_s/4"), (0.5, "f_s/2")]])
        ry = VGroup(*[Text(f"{v}", font_size=16, color=COR_EIXO).next_to(ax.c2p(0, v), LEFT, buff=0.1)
                      for v in (0, -30, -60, -90)])
        r_db = Text("|H| (dB)", font_size=16, color=COR_EIXO).next_to(ax.c2p(0, 5), UP, buff=0.1)
        casos = [(11, COR_IIR), (31, COR_H), (101, COR_Y)]
        curvas, rots = VGroup(), VGroup()
        for k, (N, cor) in enumerate(casos):
            db = np.clip(resposta_db(passa_baixa_janelado(N), f), -90, 5)
            curvas.add(VMobject().set_points_as_corners([ax.c2p(a, b) for a, b in zip(f, db)]).set_stroke(cor, 4))
            rots.add(Text(f"N = {N} taps", font_size=20, color=cor))
        rots.arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(P(5.3, 1.0))

        leg = self.legenda("O mesmo passa-baixa projetado com números crescentes de coeficientes")
        self.play(Create(ax), FadeIn(marcas), FadeIn(ry), FadeIn(r_db))
        for c, r in zip(curvas, rots):
            self.play(Create(c), FadeIn(r), run_time=1.8)
            self.wait(0.4)
        leg = self.legenda("Mais taps: transição mais estreita e rejeição maior", leg, COR_Y)
        self.wait(1)
        nota = Text("cada tap = um\nmultiplicador (ou um\nciclo de processador)", font_size=18,
                    color=COR_RUIDO).move_to(P(5.3, -0.5))
        leg = self.legenda("Desvantagem: um IIR faria corte parecido com pouquíssima matemática", leg, COR_RUIDO)
        self.play(FadeIn(nota))
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 7
    def cena_fir_iir(self):
        self.titulo_cena("7 · FIR × IIR")
        eqs = VGroup(
            tex(r"\text{FIR:}\ y[n] = \sum_k b_k\,x[n-k]", COR_Y, 30),
            tex(r"\text{IIR:}\ y[n] = \sum_k b_k\,x[n-k] - \sum_k a_k\,y[n-k]", COR_IIR, 30),
        ).arrange(RIGHT, buff=1.0).move_to(P(0, 2.45))
        xs = [-4.6, -0.6, 3.9]
        cab = VGroup(Text("Característica", font_size=22, color=GREY_A, weight=BOLD),
                     Text("FIR", font_size=22, color=COR_Y, weight=BOLD),
                     Text("IIR", font_size=22, color=COR_IIR, weight=BOLD))
        for t, x in zip(cab, xs):
            t.move_to(P(x, 1.55))
        linhas = [
            ("Realimentação", "não: só usa as entradas", "sim: usa as saídas anteriores"),
            ("Estabilidade", "sempre estável", "pode ficar instável"),
            ("Fase", "linear: a forma não se deforma", "não linear: pode distorcer"),
            ("Custo computacional", "alto para cortes abruptos", "baixo: poucos coeficientes"),
        ]
        ys = [0.75, -0.15, -1.05, -1.95]
        self.play(Write(eqs), run_time=2)
        leg = self.legenda("A diferença fundamental: realimentação")
        self.play(LaggedStart(*[FadeIn(t) for t in cab], lag_ratio=0.2))
        for (a, b, c), y in zip(linhas, ys):
            sep = Line(P(-6.6, y + 0.45), P(6.6, y + 0.45), color=COR_EIXO, stroke_width=1.5)
            linha = VGroup(Text(a, font_size=20, color=GREY_A).move_to(P(xs[0], y)),
                           Text(b, font_size=20, color=COR_Y).move_to(P(xs[1], y)),
                           Text(c, font_size=20, color=COR_IIR).move_to(P(xs[2], y)))
            self.play(Create(sep), FadeIn(linha, shift=UP * 0.1), run_time=0.8)
            self.wait(0.6)
        leg = self.legenda("Por isso o FIR domina quando forma do sinal e estabilidade importam", leg, COR_Y)
        self.wait(2)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo")
        itens = VGroup(*[Text(t, font_size=23, color=c) for t, c in [
            ("• y[n] = Σ h[k]·x[n−k]: média ponderada das últimas N amostras", COR_Y),
            ("• Estrutura: linha de atrasos + multiplicadores + somador (só para a frente)", COR_ATRASO),
            ("• Resposta ao impulso finita: dura N amostras e zera", COR_H),
            ("• Sempre estável e com fase linear: só atrasa, não deforma", COR_Y),
            ("• Mais taps: mais suave e corte mais abrupto, porém mais atraso e mais hardware", COR_RUIDO),
            ("• IIR: realimentação, barato, mas pode ser instável e distorcer a fase", COR_IIR),
        ]]).arrange(DOWN, aligned_edge=LEFT, buff=0.32).move_to(P(0, -0.2))
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.2) for t in itens], lag_ratio=0.3), run_time=3.5)
        self.wait(3)
        self.limpar()
