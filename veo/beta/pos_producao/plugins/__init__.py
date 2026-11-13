"""Plugins de pos-producao. Cada arquivo expoe processar(input, output, meta) -> bool.

Convencoes:
  - input_mp4: caminho do mp4 atual (vai sendo atualizado pelo runner)
  - output_mp4: caminho do mp4 saida deste plugin
  - meta: dict com keys 'path', 'stem', 'duracao_s', 'tem_audio', 'w', 'h'
  - Retornar True se gerou saida com sucesso, False se pulou
  - Se precisar de GPU, levantar NotImplementedError("requer GPU") - runner trata
"""
