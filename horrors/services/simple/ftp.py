from horrors import (
    logging,
    triggers,
    services,
)


__all__ = ['FTPReader']


class FTPReader(services.Service):

    address = '0.0.0.0'
    port = 2121
    banner = 'FTPReader'

    async def handler(self, reader, writer):
        writer.write(b'220 ' + bytes(self.banner, 'latin-1') + b'\r\n')
        await writer.drain()
        while True:
            data = await reader.readline()
            if not data:
                break
            data = data.decode()
            self.process(triggers.DataMatch, data)
            logging.debug(rf'Received:\r\n{data}')
            if data.startswith('USER'):
                self.process(triggers.UsernameContains, data)
                writer.write(b'331 Enter password\r\n')
            elif data.startswith('PASS'):
                self.process(triggers.PasswordContains, data)
                writer.write(b'250 Okay\r\n')
            elif data.startswith('SYST'):
                writer.write(b'215 Windows_NT\r\n')
            elif data.startswith('RETR'):
                writer.write(b'250 Continue\r\n')
            elif data.startswith('CWD'):
                writer.write(b'250 Okay\r\n')
            elif data.startswith(('TYPE', 'PASV', 'EPSV', 'EPRT', 'PORT', 'LIST')):
                writer.write(b'200 Command OK\r\n')
            elif data.startswith('QUIT'):
                writer.write(b'221 Goodbye!\r\n')
                await writer.drain()
                break
            await writer.drain()
        writer.write_eof()
        writer.close()