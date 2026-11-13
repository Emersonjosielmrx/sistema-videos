"""Micro SOCKS5 proxy server (sem autenticação, só para uso local via túnel SSH)."""
import asyncio, socket, struct, sys

async def handle(reader, writer):
    try:
        header = await reader.readexactly(2)
        ver, nmethods = struct.unpack("!BB", header)
        if ver != 5:
            writer.close()
            return
        await reader.readexactly(nmethods)
        writer.write(b"\x05\x00")
        await writer.drain()

        req = await reader.readexactly(4)
        ver, cmd, _, atyp = struct.unpack("!BBBB", req)
        if cmd != 1:
            writer.write(b"\x05\x07\x00\x01" + b"\x00" * 6)
            writer.close()
            return

        if atyp == 1:
            addr = socket.inet_ntoa(await reader.readexactly(4))
        elif atyp == 3:
            length = (await reader.readexactly(1))[0]
            addr = (await reader.readexactly(length)).decode()
        elif atyp == 4:
            addr = socket.inet_ntop(socket.AF_INET6, await reader.readexactly(16))
        else:
            writer.write(b"\x05\x08\x00\x01" + b"\x00" * 6)
            writer.close()
            return

        port = struct.unpack("!H", await reader.readexactly(2))[0]

        try:
            remote_reader, remote_writer = await asyncio.wait_for(
                asyncio.open_connection(addr, port), timeout=10
            )
        except Exception:
            writer.write(b"\x05\x05\x00\x01" + b"\x00" * 6)
            writer.close()
            return

        writer.write(b"\x05\x00\x00\x01" + b"\x00" * 4 + b"\x00\x00")
        await writer.drain()

        await asyncio.gather(
            _pipe(reader, remote_writer),
            _pipe(remote_reader, writer),
        )
    except Exception:
        pass
    finally:
        writer.close()

async def _pipe(r, w):
    try:
        while True:
            data = await r.read(65536)
            if not data:
                break
            w.write(data)
            await w.drain()
    except Exception:
        pass
    finally:
        w.close()

async def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 1080
    server = await asyncio.start_server(handle, "127.0.0.1", port)
    print(f"SOCKS5 proxy em 127.0.0.1:{port}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
