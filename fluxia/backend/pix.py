def crc16_ccitt(data: str) -> str:
    crc = 0xFFFF
    for ch in data:
        crc ^= ord(ch) << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if (crc & 0x8000) else (crc << 1)
            crc &= 0xFFFF
    return format(crc, "04X")


def emv(tag_id: str, value: str) -> str:
    return f"{tag_id}{len(value):02d}{value}"


def gerar_pix_copia_cola(
    chave_pix: str,
    nome_recebedor: str,
    cidade: str,
    valor: float,
    txid: str = "***",
) -> str:
    """Gera código Pix Copia e Cola (BR Code EMV) sem API externa."""
    gui = "br.gov.bcb.pix"
    merchant_account = emv("00", gui) + emv("01", chave_pix)

    payload = ""
    payload += emv("00", "01")  # formato
    payload += emv("01", "12")  # indicador ponto de venda (dinâmico: "12")
    payload += emv("26", merchant_account)
    payload += emv("52", "0000")  # MCC
    payload += emv("53", "986")  # moeda BRL
    if valor > 0:
        payload += emv("54", f"{valor:.2f}")
    payload += emv("58", "BR")  # país
    payload += emv("59", nome_recebedor[:25])
    payload += emv("60", cidade[:15])
    payload += emv("62", emv("05", txid[:25]))
    payload += "6304"  # tag CRC sem valor ainda

    crc = crc16_ccitt(payload)
    return payload + crc
