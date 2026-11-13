def formatar(seg):
    """H:MM:SS a partir de 1 hora, senão M:SS."""
    if seg >= 3600:
        horas = seg // 3600
        minutos = seg // 60
        return f"{horas}:{minutos:02d}:{seg % 60:02d}"
    return f"{seg // 60}:{seg % 60:02d}"
