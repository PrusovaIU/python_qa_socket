from http import HTTPStatus, client as http_client
from re import match
from typing import Optional, Tuple, Dict, Any
import logging
import socket


class _ParseError(Exception):
    pass


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

    def get_connection(self) -> (socket.socket, Tuple[str, int]):
        client, client_address = self.__socket.accept()
        self.__logger.info(f"Request from: {client_address}")
        return client, client_address


class HTTPServer:
    HTTP_VER = "1.1"
    __METHOD = "method"
    __STATUS = "status"
    __HEADERS = "headers"

    def __init__(self, address: Tuple[str, int]):
        self.__address = address
        self.__logger = logging.getLogger("HTTPServer")

    def __communicate(self, server_socket: _HTTPServerSocket):
        client_socket, client_address = server_socket.get_connection()
        try:
            with client_socket:
                data = client_socket.recv(1024)
                if data:
                    answer = self.__handle_data_from_client(data, client_address)
                    client_socket.sendall(answer)
        except OSError as err:
            self.__logger.error(f"Client {client_address} error: {err}")
        finally:
            self.__logger.info(f"Client {client_address} disconnect")

    def __handle_data_from_client(self, request: bytes, client: (str, int)) -> bytes:
        status = HTTPStatus.BAD_REQUEST
        status_code = status.value
        status_phrase = status.phrase
        answer = str()
        try:
            request_data: Dict[str, Any] = self.__parse_request(request)
            method = request_data[self.__METHOD]
            status = request_data[self.__STATUS]
            headers = request_data[self.__HEADERS]
            status_code, status_phrase = status
            answer = f"Method: {method}{headers}"
            self.__logger.info(f"Request Method: {method}\n"
                               f"Request Source: {client}\n"
                               f"Response Status: {status_code} {status_phrase}\n"
                               f"{headers}")
        except _ParseError as err:
            self.__logger.error(f"Parse request error: {err}")
        finally:
            answer = f"HTTP/{self.HTTP_VER} {status_code} {status_phrase}\n{answer}"
        return answer.encode()

    @classmethod
    def __parse_request(cls, request: bytes) -> Dict[str, Any]:
        """
        Parse request from client
        :param request:
        :return: {
                    "method": method name [str],
                    "status": (status code [int], status phrase [str]),
                    "headers": headers [str]
                }
        :raise: _ParseError
        """
        try:
            data = request.decode()
            data_match = match(r"(\S+) /(\S*) HTTP/\d+.\d+([\s\S]*)", data)
            assert data_match is not None, "Bad request"
            method = data_match[1]
            path = data_match[2]
            headers = data_match[3]
            status_match = match(r"\?status=(\S{3})", path)
            if status_match is not None:
                status_code = int(status_match[1])
                status_phrase = http_client.responses[status_code]
            else:
                status = HTTPStatus.OK
                status_code = status.value
                status_phrase = status.phrase
        except (AssertionError, KeyError) as err:
            raise _ParseError(err)
        return {
            cls.__METHOD: method,
            cls.__STATUS: (status_code, status_phrase),
            cls.__HEADERS: headers
        }

    def run(self):
        with _HTTPServerSocket(self.__address) as server_socket:
            while True:
                self.__communicate(server_socket)
