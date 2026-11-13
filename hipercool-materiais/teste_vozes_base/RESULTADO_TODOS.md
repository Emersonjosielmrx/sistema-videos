# Teste "francisca × antonio" — todos os narradores (20/10/2026)

> **Correção:** as bases eram Thalita (no lugar da Francisca) e **Andrew** (no lugar do Antonio) — o
> `edge_tts_engine` troca as duas quando falta a variável `VOZ_CLONADA`. Ver `RESULTADO_MIKE.md` e
> `VARIACOES_POR_MOMENTO.md` (F2).

31 de 38 clones prontos em `saida_todos\` (faltaram jubertim-antonio, mangaticos, mattz e momo: falta de RAM no
momento — o PC estava renderizando). Não refeitos: o teste novo (`variacoes\`) mede o que importa com as bases certas.

## Resultado (dono ouviu) e medição do tom (RMVPE, mediana)
Dono: "nas vozes das mulheres não combinou"; nos homens = mesma voz imitando personagem maligno.

| Narrador | Natural | "francisca" (Thalita) | "antonio" (Andrew) | Faixa do "antonio" |
|---|---|---|---|---|
| billie_eilish | 185 Hz | 144 Hz (-4,4 st) | 84 Hz (-13,8 st) | voz de homem |
| rihanna | 190 Hz | 136 Hz (-5,8 st) | 82 Hz (-14,5 st) | voz de homem |
| ijax | 188 Hz | 136 Hz (-5,6 st) | 83 Hz (-14,2 st) | voz de homem |
| kkvirjao | 193 Hz | 144 Hz (-5,1 st) | 87 Hz (-13,7 st) | voz de homem |
| drezin | 179 Hz | 128 Hz (-5,8 st) | 78 Hz (-14,4 st) | voz de homem |
| doinsuka | 282 Hz | 205 Hz (-5,5 st) | 124 Hz (-14,3 st) | voz de homem |
| porao | 139 Hz | 102 Hz (-5,4 st) | 65 Hz (-13,3 st) | grave de vilão |
| omelhormanhwa | 140 Hz | 102 Hz (-5,5 st) | 65 Hz (-13,3 st) | grave de vilão |
| solem8037 | 139 Hz | 102 Hz (-5,5 st) | 68 Hz (-12,6 st) | grave de vilão |
| solemsun | 140 Hz | 101 Hz (-5,6 st) | 67 Hz (-12,8 st) | grave de vilão |
| mike | 123 Hz | 90 Hz (-5,4 st) | 59 Hz (-12,7 st) | grave de vilão |
| iki | 119 Hz | 88 Hz (-5,3 st) | 55 Hz (-13,3 st) | grave de vilão |
| guugou | 111 Hz | 82 Hz (-5,2 st) | 54 Hz (-12,5 st) | grave de vilão |
| pie | 109 Hz | 83 Hz (-4,7 st) | 54 Hz (-12,1 st) | grave de vilão |
| morgan_freeman | 105 Hz | 77 Hz (-5,4 st) | 56 Hz (-11,0 st) | grave de vilão |
| jubertim | 144 Hz | 109 Hz (-4,8 st) | — | — |

Medições completas: `medicao_tons.json`.

## Conclusão
- O efeito "vilão" é tom bem mais grave + fala mais lenta e mais reta, com o timbre do narrador mantido pelo clone.
- Nas mulheres a descida de ~14 st levou a voz pra faixa masculina (≈80 Hz) — por isso não combinou. Com descida
  menor (≈3 st) a voz continua feminina e fica mais sombria: testado em `variacoes\vilao_ab\`.
