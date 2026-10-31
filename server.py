import socket
import threading

HOST = '0.0.0.0'
PORT = 8080
MAX_FRAME_BYTES = 8 * 1024 * 1024

clients = []
clients_lock = threading.Lock()
broadcast_lock = threading.Lock()


def broadcast(data, exclude_socket=None):
   with broadcast_lock:
       with clients_lock:
           recipients = [client for client in clients if client != exclude_socket]
       disconnected = []
       for client in recipients:
           try:
               client.sendall(data)
           except OSError as error:
               print(f"Не вдалося надіслати повідомлення клієнту: {error}")
               disconnected.append(client)
       if disconnected:
           with clients_lock:
               for client in disconnected:
                   if client in clients:
                       clients.remove(client)


def handle_client(client_socket):
   buffer = b''
   while True:
       try:
           data = client_socket.recv(4096)
           if not data:
               break
           buffer += data
           if len(buffer) > MAX_FRAME_BYTES and b'\n' not in buffer:
               print("Клієнт надіслав повідомлення завеликого розміру.")
               break
           oversized_frame = False
           while b'\n' in buffer:
               frame, buffer = buffer.split(b'\n', 1)
               if len(frame) > MAX_FRAME_BYTES:
                   print("Клієнт надіслав повідомлення завеликого розміру.")
                   oversized_frame = True
                   break
               broadcast(frame + b'\n', exclude_socket=client_socket)
           if oversized_frame:
               break
       except OSError as error:
           print(f"Помилка з'єднання з клієнтом: {error}")
           break
   with clients_lock:
       if client_socket in clients:
           clients.remove(client_socket)
   client_socket.close()


def main():
   server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
   server_socket.bind((HOST, PORT))
   server_socket.listen(5)
   print(f"Сервер запущено на {HOST}:{PORT}")

   while True:
       client_socket, addr = server_socket.accept()
       print(f"Підключився клієнт: {addr}")
       with clients_lock:
           clients.append(client_socket)

       t = threading.Thread(
           target=handle_client, args=(client_socket,), daemon=True
       )
       t.start()


if __name__ == "__main__":
   main()
