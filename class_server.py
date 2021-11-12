from typing import Optional, Tuple
import logging
import socket


class _HTTPServerSocket:
    def __init__(self, address: Tuple[str, int]):
        self.__socket: Optional[socket.socket] = None
        self.__address = address
        self.__logger = logging.getLogger("HTTPServerSocket")

    def __enter__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(self.__address)
        sock.listen()
        self.__socket = sock
        self.__logger.info(f"Run on {self.__socket.getsockname()}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.__socket, socket.socket):
            self.__socket.close()

    def get_connection(self) -> socket.socket:
        client, client_address = self.__socket.accept()
        self.__logger.info(f"New client: {client_address}")
        return client


class HTTPServer:
    def __init__(self, address: Tuple[str, int]):
        self.__address = address
        self.__logger = logging.getLogger("HTTPServer")

    def run(self):
        with _HTTPServerSocket(self.__address) as server_socket:
            while True:
                client_socket: socket.socket = server_socket.get_connection()
                with client_socket:
                    data: Optional[bytes] = None
                    while data is None or len(data) > 0:
                        data = client_socket.recv(1024)
                        a = data.decode()
                        print(data.decode())
                    self.__logger.info("Client disconnect")


