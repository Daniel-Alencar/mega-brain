# -*- coding: utf-8 -*-
"""
Non-IQ sampling: N amostras em M períodos e estimação por mínimos quadrados
===========================================================================

Renderização (a partir da raiz do repositório):
    manim -pql "src/Detecção de amplitude e fase em RF/Non-IQ sampling/non_iq_sampling.py" NonIQSampling   # rascunho
    manim -pqh "src/Detecção de amplitude e fase em RF/Non-IQ sampling/non_iq_sampling.py" NonIQSampling   # final

Requer LaTeX (MathTex).

Roteiro (segue "docs/Detecção de amplitude e fase em RF/Non-IQ sampling"):
    Abertura
    Cena 1 - Motivação: no IQ sampling as harmônicas ímpares caem sobre f_IF
    Cena 2 - Conceito: f_s/f_IF = N/M, passo Δφ = 2π·M/N, N pontos distintos no círculo
    Cena 3 - Sistema sobredeterminado e função de custo f(I, Q)
    Cena 4 - Por que fica simples: Σ e^{j2φi} = 0 ⇒ p12 = 0 e p11 = p22 = N/2
    Cena 5 - O estimador final: médias ponderadas com coeficientes de uma LUT
    Cena 6 - Vantagem: harmônicas espalhadas fora da portadora
    Cena 7 - Vantagem: média sobre N pontos (ruído menor, offset DC cancelado)
    Cena 8 - O preço: latência de N amostras
    Resumo

Exemplo numérico usado: N = 9, M = 2  ⇒  f_s = 4,5·f_IF,  Δφ = 80°.
Convenção:
    y_i = A·sin(φ0 + i·Δφ) = I·sin(φ_i) + Q·cos(φ_i),  φ_i = i·Δφ
    I = (2/N)·Σ y_i·sin(φ_i),   Q = (2/N)·Σ y_i·cos(φ_i)
"""

import numpy as np
from manim import *

# Paleta didática (fixa em todas as cenas)
COR_RF = BLUE            # fasor / sinal de IF
COR_I = GOLD             # componente I
COR_Q = GREEN            # componente Q
COR_AMOSTRA = WHITE      # amostras do ADC
COR_ERRO = RED           # ruído, resíduos, harmônicas sobre a portadora
COR_IQ = ORANGE          # IQ sampling clássico (comparação)
COR_DIGITAL = TEAL       # Non-IQ / processamento digital
COR_FILTRO = PINK
COR_EIXO = GREY_B
FUNDO = "#0e1117"

EIXO_CFG = {"include_tip": False, "stroke_width": 2, "color": COR_EIXO}
N, M = 9, 2
DPHI = TAU * M / N                         # 80°
FI0 = np.deg2rad(35)
I0, Q0 = np.cos(FI0), np.sin(FI0)          # A = 1
SIGMA = 0.12                               # ruído das amostras (ilustrativo)
ALTURAS = [0, 1.0, 0.55, 0.5, 0.42, 0.36, 0.3, 0.26]   # amplitudes das harmônicas (ilustrativas)

FASES = np.arange(N) * DPHI
_rng = np.random.default_rng(23)
AMOSTRAS = I0 * np.sin(FASES) + Q0 * np.cos(FASES) + SIGMA * _rng.standard_normal(N)
I_EST = 2 / N * np.sum(AMOSTRAS * np.sin(FASES))
Q_EST = 2 / N * np.sum(AMOSTRAS * np.cos(FASES))


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


def tracejada(a, b, cor, largura=3):
    if np.linalg.norm(b - a) < 0.05:
        return VMobject()
    return DashedLine(a, b, color=cor, stroke_width=largura, dash_length=0.08)


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


def estimar_nao_iq(amostras):
    return (2 / N * np.sum(amostras * np.sin(FASES)), 2 / N * np.sum(amostras * np.cos(FASES)))


# =============================================================================
# Cena
# =============================================================================
class NonIQSampling(Scene):
    def construct(self):
        self.camera.background_color = FUNDO
        self.abertura()
        self.cena_motivacao()
        self.cena_conceito()
        self.cena_sistema()
        self.cena_simplificacao()
        self.cena_estimador()
        self.cena_harmonicas()
        self.cena_ruido()
        self.cena_latencia()
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

    def espectro_harmonicas(self, fs, textos, leg, y0=0.6, cor_ok=GREY_B):
        """Monta as harmônicas de f_IF e anima o rebatimento (aliasing) para [0, f_s/2].

        textos = (antes de mostrar Nyquist, ao mostrar Nyquist, depois de rebater)."""
        ax = Axes(x_range=[0, 7.6, 1], y_range=[0, 1.25, 0.5], x_length=12.4, y_length=2.3,
                  axis_config={"include_tip": True, "stroke_width": 2, "color": COR_EIXO},
                  y_axis_config={"include_tip": False}).move_to(P(0, y0))
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

        leg = self.legenda(textos[0], leg)
        self.play(Create(ax), FadeIn(marcas), FadeIn(rot_f))
        self.play(GrowArrow(raias[1]), FadeIn(rots[1]))
        self.play(LaggedStart(*[AnimationGroup(GrowArrow(raias[k]), FadeIn(rots[k])) for k in range(2, 8)],
                              lag_ratio=0.2), run_time=1.8)
        leg = self.legenda(textos[1], leg, COR_DIGITAL)
        self.play(FadeIn(zona), Create(l_nyq), FadeIn(r_nyq), Create(l_fs), FadeIn(r_fs))

        pos, grupos = posicoes_alias(fs)
        novos = {}
        anims = []
        for k in range(2, 8):
            cai = abs(alias(k, fs) - 1) < 1e-6
            novos[k] = raia(ax, pos[k], ALTURAS[k], COR_ERRO if cai else cor_ok)
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
        leg = self.legenda(textos[2], leg, COR_ERRO if any(abs(alias(k, fs) - 1) < 1e-6 for k in range(2, 8))
                           else COR_DIGITAL)
        grupo = VGroup(ax, marcas, rot_f, zona, l_nyq, r_nyq, l_fs, r_fs, raias[1], rots[1],
                       *novos.values(), rot_grupos)
        return grupo, leg, ax, novos

    # ---------------------------------------------------------------- abertura
    def abertura(self):
        titulo = Text("Non-IQ sampling", font_size=60, weight=BOLD)
        sub = Text("N amostras em M períodos e estimação por mínimos quadrados", font_size=30, color=GREY_A)
        razao = tex(r"\frac{f_s}{f_{IF}} = \frac{N}{M}", COR_DIGITAL, 44)
        g = VGroup(titulo, sub, razao).arrange(DOWN, buff=0.35)
        self.play(Write(titulo), run_time=1.5)
        self.play(FadeIn(sub, shift=UP * 0.2), FadeIn(razao, shift=UP * 0.2))
        self.wait(1.2)
        self.play(FadeOut(g))

    # ================================================================== CENA 1
    def cena_motivacao(self):
        self.titulo_cena("1 · O problema do IQ sampling")
        _, leg, _, novos = self.espectro_harmonicas(
            4.0,
            ("Mixers e ADCs não lineares geram harmônicas de f_IF",
             "IQ sampling: f_s = 4·f_IF, tudo acima de 2·f_IF dobra para dentro",
             "As harmônicas ímpares caem exatamente em cima de f_IF"),
            None, y0=0.4)
        self.play(*[Indicate(novos[k], color=COR_ERRO) for k in (3, 5, 7)])
        leg = self.legenda("Mesma frequência do sinal útil: impossível distinguir ou filtrar", leg, COR_ERRO)
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 2
    def cena_conceito(self):
        self.titulo_cena("2 · Conceito: N amostras em M períodos")
        f1 = tex(r"\frac{f_s}{f_{IF}} = \frac{N}{M} \iff N\,T_s = M\,T_{IF}", WHITE, 30).move_to(P(-3.4, 2.3))
        f2 = tex(r"\Delta\varphi = \omega_{IF} T_s = 2\pi\frac{M}{N}", WHITE, 30).move_to(P(3.3, 2.45))
        ex = tex(r"N = 9,\ M = 2 \;\Rightarrow\; \Delta\varphi = 80^\circ", COR_DIGITAL, 28
                 ).next_to(f2, DOWN, buff=0.15)

        eixos, rotulos = plano(P(-4.4, -0.8), 3.2, 1.3)
        o = eixos.c2p(0, 0)
        raio = eixos.c2p(1, 0)[0] - o[0]
        circulo = DashedVMobject(Circle(radius=raio, color=COR_EIXO).move_to(o), num_dashes=40).set_stroke(width=2)
        ax = eixos_tempo(P(2.3, -0.8), 7.4, 3.2, [0, 2, 0.25], [-1.3, 1.3, 0.5])
        rot_t = Text("tempo (períodos de IF) →", font_size=18, color=COR_EIXO).next_to(ax, DOWN, buff=0.05
                                                                                        ).align_to(ax, RIGHT)
        onda = ax.plot(lambda x: np.sin(TAU * x + FI0), x_range=[0, 2, 0.01], color=COR_RF,
                       stroke_width=3).set_stroke(opacity=0.45)
        k_val = ValueTracker(0.0)

        def ang():
            return FI0 + k_val.get_value() * DPHI

        def ponta():
            return eixos.c2p(np.cos(ang()), np.sin(ang()))

        fasor = always_redraw(lambda: seta(o, ponta(), COR_RF, 6))
        proj = always_redraw(lambda: tracejada(ponta(), ax.c2p(k_val.get_value() * M / N, np.sin(ang())), GREY_A, 2))

        fantasmas = VGroup(*[Dot(eixos.c2p(np.cos(FI0 + k * PI / 2), np.sin(FI0 + k * PI / 2)), radius=0.1,
                                 color=COR_IQ).set_opacity(0.7) for k in range(4)])
        rot_fant = Text("IQ sampling: sempre os mesmos 4 pontos", font_size=18, color=COR_IQ
                        ).next_to(eixos, DOWN, buff=0.1)

        leg = self.legenda("No IQ sampling clássico, as amostras caem sempre nos mesmos 4 pontos do ciclo")
        self.play(Create(eixos), FadeIn(rotulos), Create(circulo))
        self.play(LaggedStart(*[GrowFromCenter(d) for d in fantasmas], lag_ratio=0.2), FadeIn(rot_fant))
        leg = self.legenda("Non-IQ: N amostras espalhadas ao longo de M períodos da IF", leg, COR_DIGITAL)
        self.play(Write(f1), run_time=1.5)
        self.play(Write(f2), FadeIn(ex))
        self.play(Create(ax), FadeIn(rot_t), Create(onda))
        self.add(fasor, proj)
        self.play(FadeOut(fantasmas), FadeOut(rot_fant))

        leg = self.legenda("A cada amostra o fasor avança 80°: os pontos não se repetem", leg)
        for i in range(N + 1):
            if i > 0:
                self.play(k_val.animate.set_value(i), run_time=0.7 if i < 4 else 0.4)
            a = FI0 + i * DPHI
            y = np.sin(a)
            cor = WHITE if i == N else COR_DIGITAL
            ponto = Dot(eixos.c2p(np.cos(a), np.sin(a)), radius=0.08, color=cor)
            h = haste(ax, i * M / N, y, cor, 0.07, 3)
            anims = [GrowFromCenter(ponto), GrowFromPoint(h, ax.c2p(i * M / N, 0))]
            if i < N:
                anims.append(FadeIn(Text(str(i), font_size=16, color=COR_DIGITAL).move_to(
                    eixos.c2p(1.22 * np.cos(a), 1.22 * np.sin(a)))))
            self.play(*anims, run_time=0.5 if i < 4 else 0.3)
            if i == N:
                self.play(Flash(ponto, color=WHITE), Indicate(h, color=WHITE))
        leg = self.legenda("9 pontos distintos no círculo; o padrão só se repete após M = 2 períodos", leg,
                           COR_DIGITAL)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 3
    def cena_sistema(self):
        self.titulo_cena("3 · Estimação por mínimos quadrados")
        ax = eixos_tempo(P(0, 1.3), 12, 2.1, [0, 2, 0.25], [-1.4, 1.4, 0.5])
        rot_ax = rotulo_eixo(ax, Text("amostras com ruído (branco) e modelo I·sin φ + Q·cos φ (tracejado)",
                                      font_size=20, color=GREY_A))
        xs = np.arange(N) * M / N
        ideal = ax.plot(lambda x: np.sin(TAU * x + FI0), x_range=[0, 2, 0.01], color=COR_RF,
                        stroke_width=3).set_stroke(opacity=0.35)
        pts = VGroup(*[haste(ax, x, y, COR_AMOSTRA, 0.07) for x, y in zip(xs, AMOSTRAS)])

        eq = tex_partes([(r"y_i = I\sin\varphi_i + Q\cos\varphi_i", WHITE), (r"\;+\;\text{ruído}", COR_ERRO),
                         (r",\qquad \varphi_i = i\,\Delta\varphi,\quad i = 0,\dots,N-1", GREY_A)], 30
                        ).move_to(P(0, -0.3))
        custo = tex(r"f(I,Q) = \sum_{i=0}^{N-1}\big(I\sin\varphi_i + Q\cos\varphi_i - y_i\big)^2", WHITE, 32
                    ).move_to(P(-2.6, -1.75))

        it = ValueTracker(-0.2)
        qt = ValueTracker(-0.6)

        def modelo(x):
            return it.get_value() * np.sin(TAU * x) + qt.get_value() * np.cos(TAU * x)

        def custo_atual():
            return float(np.sum((it.get_value() * np.sin(FASES) + qt.get_value() * np.cos(FASES) - AMOSTRAS) ** 2))

        curva = always_redraw(lambda: DashedVMobject(ax.plot(modelo, x_range=[0, 2, 0.01], color=COR_DIGITAL,
                                                             stroke_width=3), num_dashes=60))
        residuos = always_redraw(lambda: VGroup(*[
            Line(ax.c2p(x, y), ax.c2p(x, modelo(x)), color=COR_ERRO, stroke_width=4)
            for x, y in zip(xs, AMOSTRAS) if abs(modelo(x) - y) > 0.02]))
        painel = always_redraw(lambda: VGroup(
            Text(f"I = {it.get_value():+.2f}   Q = {qt.get_value():+.2f}", font_size=22, color=COR_DIGITAL),
            Text(f"f(I, Q) = {custo_atual():.3f}", font_size=24, color=COR_ERRO),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(P(4.3, -1.75)))

        leg = self.legenda("O ADC entrega N amostras, todas com ruído, quantização e jitter")
        self.play(Create(ax), FadeIn(rot_ax), Create(ideal))
        self.play(LaggedStart(*[GrowFromPoint(p, ax.c2p(x, 0)) for p, x in zip(pts, xs)], lag_ratio=0.12))
        leg = self.legenda("N = 9 equações para 2 incógnitas: sistema sobredeterminado", leg)
        self.play(Write(eq), run_time=1.8)
        leg = self.legenda("Melhor estimativa: o (I, Q) que minimiza a soma dos erros ao quadrado", leg, COR_DIGITAL)
        self.play(Write(custo), run_time=1.8)
        self.add(curva, residuos)
        self.play(FadeIn(painel))
        leg = self.legenda("Chute inicial ruim: resíduos grandes (vermelho)", leg, COR_ERRO)
        self.wait(0.8)
        leg = self.legenda("Ajustando I e Q, os resíduos e o custo diminuem até o mínimo", leg, COR_DIGITAL)
        self.play(it.animate.set_value(0.4), qt.animate.set_value(0.1), run_time=2)
        self.play(it.animate.set_value(I_EST), qt.animate.set_value(Q_EST), run_time=2)
        self.play(Indicate(painel, color=COR_DIGITAL))
        self.wait(1.2)
        self.limpar()

    # ================================================================== CENA 4
    def cena_simplificacao(self):
        self.titulo_cena("4 · Por que o mínimo tem forma tão simples")
        m1 = tex(r"\frac{\partial f}{\partial I} = 0,\qquad \frac{\partial f}{\partial Q} = 0", WHITE, 30)
        m2 = tex(r"\begin{pmatrix} p_{11} & p_{12} \\ p_{21} & p_{22} \end{pmatrix}"
                 r"\begin{pmatrix} I \\ Q \end{pmatrix} = \begin{pmatrix} s_1 \\ s_2 \end{pmatrix}", WHITE, 30)
        m3 = tex(r"s_1 = \sum y_i\sin\varphi_i,\qquad s_2 = \sum y_i\cos\varphi_i", GREY_A, 28)
        m4 = tex_partes([(r"p_{12} = p_{21} = \sum\sin\varphi_i\cos\varphi_i = ", WHITE),
                         (r"\tfrac{1}{2}\sum\sin 2\varphi_i", COR_DIGITAL)], 28)
        m5 = tex_partes([(r"p_{11} = \sum\sin^2\varphi_i = \tfrac{N}{2}", WHITE),
                         (r"- \tfrac{1}{2}\sum\cos 2\varphi_i", COR_DIGITAL)], 28)
        m6 = tex(r"p_{12} = p_{21} = 0,\qquad p_{11} = p_{22} = \frac{N}{2}", COR_I, 32)
        esquerda = VGroup(m1, m2, m3, m4, m5, m6).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        esquerda.to_edge(LEFT, buff=0.4).align_to(P(0, 2.9), UP)
        nota = Text("(somas de i = 0 a N − 1)", font_size=18, color=GREY_B).next_to(m3, RIGHT, buff=0.25)

        # Cadeia de vetores e^{j2φi}: fecha um polígono ⇒ soma nula
        s = 1.45
        pts = [np.zeros(2)]
        for i in range(N):
            a = 2 * FASES[i]
            pts.append(pts[-1] + s * np.array([np.cos(a), np.sin(a)]))
        pts = np.array(pts)
        centro = (pts.max(axis=0) + pts.min(axis=0)) / 2
        base = P(4.2, -0.2)

        def tela(p):
            return base + np.array([p[0] - centro[0], p[1] - centro[1], 0.0])

        cadeia = VGroup(*[Arrow(tela(pts[i]), tela(pts[i + 1]), buff=0, color=COR_DIGITAL, stroke_width=4,
                                max_tip_length_to_length_ratio=0.15) for i in range(N)])
        origem = Dot(tela(pts[0]), radius=0.08, color=WHITE)
        cab = tex(r"\sum_{i=0}^{N-1} e^{\,j2\varphi_i}", COR_DIGITAL, 32).move_to(P(4.2, 2.45))
        res = tex(r"= 0 \;\Rightarrow\; \sum\sin 2\varphi_i = \sum\cos 2\varphi_i = 0", COR_DIGITAL, 28
                  ).move_to(P(4.2, -2.55))
        expl = Text("vetores de ângulo 2φᵢ, encadeados", font_size=18, color=GREY_A).next_to(cab, DOWN, buff=0.12)

        leg = self.legenda("Derivadas parciais nulas: um sistema linear 2×2")
        self.play(Write(m1))
        self.play(Write(m2), run_time=1.5)
        self.play(FadeIn(m3), FadeIn(nota))
        leg = self.legenda("Os termos p dependem só das fases φi, conhecidas de antemão", leg)
        self.play(Write(m4), run_time=1.5)
        self.play(Write(m5), run_time=1.5)

        leg = self.legenda("Somando vetores de ângulo 2φi ao longo do ciclo completo…", leg, COR_DIGITAL)
        self.play(FadeIn(cab), FadeIn(expl), GrowFromCenter(origem))
        self.play(LaggedStart(*[GrowArrow(v) for v in cadeia], lag_ratio=0.5), run_time=4)
        self.play(Flash(origem, color=WHITE))
        leg = self.legenda("…o polígono fecha: a soma é zero (simetria das fases)", leg, COR_DIGITAL)
        self.play(Write(res))
        self.play(Indicate(m4[1], color=COR_DIGITAL), Indicate(m5[1], color=COR_DIGITAL))
        leg = self.legenda("A matriz vira diagonal: I e Q se calculam separadamente", leg, COR_I)
        self.play(Write(m6))
        self.play(Create(SurroundingRectangle(m6, color=COR_I, buff=0.1)))
        self.wait(1.5)
        self.limpar()

    # ================================================================== CENA 5
    def cena_estimador(self):
        self.titulo_cena("5 · O estimador final")
        f_i = tex_partes([(r"I = ", COR_I), (r"\frac{2}{N}\sum_{i=0}^{N-1} y_i\cdot", WHITE),
                          (r"\sin(i\,\Delta\varphi)", COR_DIGITAL)], 32).move_to(P(-3.3, 2.35))
        f_q = tex_partes([(r"Q = ", COR_Q), (r"\frac{2}{N}\sum_{i=0}^{N-1} y_i\cdot", WHITE),
                          (r"\cos(i\,\Delta\varphi)", COR_DIGITAL)], 32).move_to(P(3.3, 2.35))

        xs = [-4.6 + 1.2 * i for i in range(N)]
        linhas_y = [1.05, 0.45, -0.15]
        rot_linhas = VGroup(tex(r"y_i", WHITE, 26), tex(r"\sin(i\Delta\varphi)", COR_DIGITAL, 24),
                            tex(r"\cos(i\Delta\varphi)", COR_DIGITAL, 24))
        for r, y in zip(rot_linhas, linhas_y):
            r.move_to(P(-6.15, y))
        rot_lut = Text("LUT", font_size=18, color=COR_DIGITAL, weight=BOLD).move_to(P(-6.15, -0.6))
        celulas = VGroup()
        for i, x in enumerate(xs):
            col = VGroup(
                Text(f"{AMOSTRAS[i]:+.2f}", font_size=20, color=WHITE).move_to(P(x, linhas_y[0])),
                Text(f"{np.sin(FASES[i]):+.2f}", font_size=20, color=COR_DIGITAL).move_to(P(x, linhas_y[1])),
                Text(f"{np.cos(FASES[i]):+.2f}", font_size=20, color=COR_DIGITAL).move_to(P(x, linhas_y[2])),
            )
            celulas.add(col)
        cab_i = VGroup(*[Text(f"i={i}", font_size=16, color=GREY_B).move_to(P(x, 1.55)) for i, x in enumerate(xs)])

        k = ValueTracker(-1)

        def acumuladores():
            n = int(round(k.get_value()))
            si = float(np.sum(AMOSTRAS[:n + 1] * np.sin(FASES[:n + 1]))) if n >= 0 else 0.0
            sq = float(np.sum(AMOSTRAS[:n + 1] * np.cos(FASES[:n + 1]))) if n >= 0 else 0.0
            return VGroup(
                Text(f"Σ y·sin = {si:+.3f}", font_size=24, color=COR_I),
                Text(f"Σ y·cos = {sq:+.3f}", font_size=24, color=COR_Q),
            ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(P(-3.6, -1.6))

        acc = always_redraw(acumuladores)
        janela = Rectangle(width=1.05, height=1.85, color=WHITE, stroke_width=3).move_to(P(xs[0], linhas_y[1]))

        eixos, rotulos = plano(P(4.6, -1.85), 2.4, 1.2)
        o = eixos.c2p(0, 0)
        real = seta(o, eixos.c2p(I0, Q0), COR_RF, 5)
        est = Dot(eixos.c2p(I_EST, Q_EST), radius=0.08, color=COR_DIGITAL)

        leg = self.legenda("Com a matriz diagonal, I e Q viram médias ponderadas das amostras")
        self.play(Write(f_i), Write(f_q), run_time=2)
        leg = self.legenda("Os pesos sin(iΔφ) e cos(iΔφ) são constantes: ficam numa tabela (LUT) na FPGA",
                           leg, COR_DIGITAL)
        self.play(FadeIn(rot_linhas), FadeIn(rot_lut), FadeIn(cab_i),
                  LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in celulas], lag_ratio=0.08), run_time=2)
        leg = self.legenda("A cada amostra: multiplicar por constantes e acumular", leg)
        self.play(Create(janela), FadeIn(acc))
        for i in range(N):
            self.play(janela.animate.move_to(P(xs[i], linhas_y[1])), k.animate.set_value(i),
                      run_time=0.7 if i < 3 else 0.4)
        acc.clear_updaters()
        final = VGroup(
            Text(f"Î = (2/N)·Σ = {I_EST:.3f}   (real {I0:.3f})", font_size=22, color=COR_I),
            Text(f"Q̂ = (2/N)·Σ = {Q_EST:.3f}   (real {Q0:.3f})", font_size=22, color=COR_Q),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(P(-3.3, -2.75))
        leg = self.legenda("Depois das N amostras, multiplica-se por 2/N", leg, COR_DIGITAL)
        self.play(FadeIn(final, shift=UP * 0.1), FadeOut(janela))
        self.play(Create(eixos), FadeIn(rotulos), GrowArrow(real))
        self.play(GrowFromCenter(est), Flash(est, color=COR_DIGITAL))
        leg = self.legenda("A estimativa cai sobre o fasor real, mesmo com ruído nas amostras", leg, COR_DIGITAL)
        self.wait(1.8)
        self.limpar()

    # ================================================================== CENA 6
    def cena_harmonicas(self):
        self.titulo_cena("6 · Vantagem: harmônicas fora da portadora")
        grupo, leg, ax, novos = self.espectro_harmonicas(
            N / M,
            ("As mesmas harmônicas, agora com f_s = (N/M)·f_IF = 4,5·f_IF",
             "Nyquist em 2,25·f_IF: as harmônicas também dobram para dentro…",
             "…mas caem em 0,5, 1,5 e 2·f_IF, longe da portadora"),
            None, y0=0.7, cor_ok=COR_DIGITAL)
        mascara = Polygon(ax.c2p(0.8, 0), ax.c2p(0.8, 1.15), ax.c2p(1.2, 1.15), ax.c2p(1.2, 0),
                          color=COR_FILTRO, stroke_width=3, fill_color=COR_FILTRO, fill_opacity=0.15)
        rot_m = Text("filtro digital", font_size=18, color=COR_FILTRO).next_to(ax.c2p(1.2, 1.15), RIGHT, buff=0.1)
        leg = self.legenda("Separadas da portadora, podem ser removidas por filtros digitais", leg, COR_FILTRO)
        self.play(FadeIn(mascara), FadeIn(rot_m))
        nota = VGroup(
            tex(r"k f_{IF} \equiv \pm f_{IF} \pmod{f_s} \iff k = mN \pm 1", WHITE, 30),
            Text("As primeiras a cair sobre f_IF são a (N−1)ª e a (N+1)ª: 8ª e 10ª, bem mais fracas",
                 font_size=20, color=GREY_A),
        ).arrange(DOWN, buff=0.2).move_to(P(0, -2.2))
        leg = self.legenda("Quanto maior N, mais alta (e mais fraca) a primeira harmônica problemática", leg)
        self.play(FadeIn(nota, shift=UP * 0.2))
        self.wait(2)
        self.limpar()

    # ================================================================== CENA 7
    def cena_ruido(self):
        self.titulo_cena("7 · Vantagem: média sobre N pontos")
        rng = np.random.default_rng(11)
        n_ens = 160
        iq = np.column_stack([I0 + SIGMA * rng.standard_normal(n_ens), Q0 + SIGMA * rng.standard_normal(n_ens)])
        nao = np.array([estimar_nao_iq(I0 * np.sin(FASES) + Q0 * np.cos(FASES) + SIGMA * rng.standard_normal(N))
                        for _ in range(n_ens)])
        lados = [(-3.4, "IQ sampling: 2 amostras", COR_IQ, iq), (3.4, f"Non-IQ: N = {N} amostras", COR_DIGITAL, nao)]
        grupos = []
        for x, nome, cor, nuvem in lados:
            eixos, rot = plano(P(x, -0.6), 3.6, 1.3)
            o = eixos.c2p(0, 0)
            cab = Text(nome, font_size=26, color=cor, weight=BOLD).next_to(eixos, UP, buff=0.3)
            real = seta(o, eixos.c2p(I0, Q0), COR_RF, 5)
            pontos = VGroup(*[Dot(eixos.c2p(*p), radius=0.03, color=cor) for p in nuvem]).set_opacity(0.8)
            dp = np.sqrt(np.mean(np.sum((nuvem - [I0, Q0]) ** 2, axis=1)) / 2)
            txt = Text(f"desvio por componente ≈ {dp:.3f}", font_size=20, color=cor).next_to(eixos, DOWN, buff=0.1)
            grupos.append((eixos, rot, cab, real, pontos, txt))

        leg = self.legenda(f"Mesmo ruído nas amostras (σ = {SIGMA}): repetimos a medida {n_ens} vezes")
        for eixos, rot, cab, real, pontos, txt in grupos:
            self.play(FadeIn(cab), Create(eixos), FadeIn(rot), GrowArrow(real), run_time=1)
        for eixos, rot, cab, real, pontos, txt in grupos:
            self.play(LaggedStart(*[FadeIn(p) for p in pontos], lag_ratio=0.01), run_time=2)
            self.play(FadeIn(txt))
        formula = tex(r"\sigma_{I,Q} \approx \sigma\sqrt{2/N}", COR_DIGITAL, 30).move_to(P(5.0, 2.55))
        leg = self.legenda("A média sobre N pontos do círculo reduz o ruído (e quantização, DNL/INL, jitter)",
                           leg, COR_DIGITAL)
        self.play(Write(formula))
        self.wait(1)
        offset = tex(r"\textstyle\sum_i c\,\sin(i\Delta\varphi) = \sum_i c\,\cos(i\Delta\varphi) = 0",
                     COR_I, 28).move_to(P(0.6, 2.55))
        leg = self.legenda("Offset DC: as somas de seno e cosseno no ciclo completo são nulas e o cancelam", leg,
                           COR_I)
        self.play(Write(offset))
        self.wait(2)
        self.limpar()

    # ================================================================== CENA 8
    def cena_latencia(self):
        self.titulo_cena("8 · O preço: latência")
        nmax = 20
        dx = 0.55
        x0 = -5.2

        def xpos(n):
            return x0 + dx * n

        cursor = ValueTracker(-0.5)
        filas = [(1.2, "IQ sampling", COR_IQ), (-1.2, f"Non-IQ (N = {N})", COR_DIGITAL)]
        estaticos = VGroup()
        for y, nome, cor in filas:
            estaticos.add(Line(P(xpos(0) - 0.3, y), P(xpos(nmax) + 0.3, y), color=COR_EIXO, stroke_width=2))
            estaticos.add(Text(nome, font_size=22, color=cor, weight=BOLD).move_to(P(-6.0, y + 0.75)).align_to(
                P(-6.8, 0), LEFT))
        rot_n = Text("amostras do ADC →", font_size=18, color=COR_EIXO).move_to(P(4.6, -2.55))

        def amostras(y):
            c = cursor.get_value()
            return VGroup(*[Dot(P(xpos(n), y), radius=0.07, color=WHITE if n <= c else GREY_D)
                            for n in range(nmax + 1)])

        def janela_iq():
            c = cursor.get_value()
            if c < 1:
                return VMobject()
            n = int(np.floor(c))
            return Rectangle(width=dx + 0.3, height=0.5, color=COR_IQ, stroke_width=3).move_to(
                P((xpos(n - 1) + xpos(n)) / 2, 1.2))

        def janela_nao():
            c = cursor.get_value()
            if c < 0:
                return VMobject()
            n = int(np.floor(c))
            ini = (n // N) * N
            return Rectangle(width=xpos(n) - xpos(ini) + 0.3, height=0.5, color=COR_DIGITAL, stroke_width=3
                             ).move_to(P((xpos(ini) + xpos(n)) / 2, -1.2))

        def saidas_iq():
            c = cursor.get_value()
            return VGroup(*[Triangle(color=COR_IQ, fill_opacity=1).scale(0.09).rotate(PI).move_to(P(xpos(n), 1.62))
                            for n in range(1, nmax + 1) if n <= c])

        def saidas_nao():
            c = cursor.get_value()
            return VGroup(*[Triangle(color=COR_DIGITAL, fill_opacity=1).scale(0.14).rotate(PI).move_to(
                P(xpos(n), -0.75)) for n in range(N - 1, nmax + 1, N) if n <= c])

        linha_t = always_redraw(lambda: DashedLine(P(xpos(cursor.get_value()), 2.1), P(xpos(cursor.get_value()), -1.9),
                                                   color=GREY_A, stroke_width=2))
        dinamicos = [always_redraw(lambda: amostras(1.2)), always_redraw(lambda: amostras(-1.2)),
                     always_redraw(janela_iq), always_redraw(janela_nao), always_redraw(saidas_iq),
                     always_redraw(saidas_nao), linha_t]
        notas = VGroup(
            Text("nova estimativa a cada amostra (janela de 2)", font_size=18, color=COR_IQ).move_to(P(1.5, 2.2)),
            Text("uma estimativa a cada N amostras (+ atraso de grupo dos filtros)", font_size=18,
                 color=COR_DIGITAL).move_to(P(1.5, -1.95)),
        )
        leg = self.legenda("▼ = momento em que um novo (I, Q) fica disponível")
        self.play(FadeIn(estaticos), FadeIn(rot_n))
        self.add(*dinamicos)
        self.play(FadeIn(notas))
        self.play(cursor.animate.set_value(nmax), run_time=9, rate_func=linear)
        leg = self.legenda("IQ: 2 amostras bastam. Non-IQ: é preciso esperar as N amostras", leg, COR_IQ)
        self.wait(1.5)
        leg = self.legenda("Malhas ultrarrápidas preferem IQ; precisão e linearidade pedem Non-IQ", leg)
        self.wait(1.5)
        self.limpar()

    # ================================================================== RESUMO
    def cena_resumo(self):
        self.titulo_cena("Resumo: IQ × Non-IQ sampling")
        xs = [-4.5, -0.6, 3.8]
        cab = VGroup(
            Text("Característica", font_size=22, color=GREY_A, weight=BOLD),
            Text("IQ sampling (f_s = 4·f_IF)", font_size=22, color=COR_IQ, weight=BOLD),
            Text("Non-IQ (f_s/f_IF = N/M)", font_size=22, color=COR_DIGITAL, weight=BOLD),
        )
        for t, x in zip(cab, xs):
            t.move_to(P(x, 2.35))
        linhas_txt = [
            ("Amostras por\nestimativa", "2", "N"),
            ("Harmônicas", "ímpares caem sobre f_IF", "espalhadas, filtráveis"),
            ("Ruído, offset,\nDNL/INL", "entram direto na medida", "atenuados pela média\n(offset cancela)"),
            ("Latência", "mínima", "N amostras + filtros"),
            ("Uso típico", "malhas ultrarrápidas", "precisão e linearidade"),
        ]
        ys = [1.4, 0.4, -0.65, -1.7, -2.6]
        cores = [GREY_A, COR_IQ, COR_DIGITAL]
        self.play(LaggedStart(*[FadeIn(t, shift=DOWN * 0.1) for t in cab], lag_ratio=0.2))
        for (a, b, c), y in zip(linhas_txt, ys):
            sep = Line(P(-6.6, y + 0.5), P(6.6, y + 0.5), color=COR_EIXO, stroke_width=1.5)
            linha = VGroup(*[Text(t, font_size=20, color=cor, line_spacing=1.1).move_to(P(x, y))
                             for t, cor, x in zip((a, b, c), cores, xs)])
            self.play(Create(sep), FadeIn(linha, shift=UP * 0.1), run_time=0.8)
            self.wait(0.6)
        self.wait(2.5)
        self.limpar()
