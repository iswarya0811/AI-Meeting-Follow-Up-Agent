import socket
import threading
import os

def handle_client(conn, addr):
    try:
        conn.sendall(b"220 Mock SMTP Server Ready\r\n")
        data_mode = False
        email_content = []
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            if data_mode:
                content_str = data.decode('utf-8', errors='ignore')
                email_content.append(content_str)
                # Check for the end of DATA indicator (CRLF.CRLF)
                full_data = "".join(email_content)
                if "\r\n.\r\n" in full_data or full_data.endswith("\r\n.\r\n"):
                    conn.sendall(b"250 OK - message received\r\n")
                    data_mode = False
                    
                    # Print received email to console log
                    clean_content = full_data.replace("\r\n", "\n")
                    print(f"\n[MOCK SMTP] Received email from client at {addr}:")
                    print("-" * 50)
                    print(clean_content)
                    print("-" * 50)
                    
                    # Save to received_emails.log file
                    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received_emails.log")
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"=== EMAIL RECEIVED FROM CLIENT {addr} ===\n")
                        f.write(clean_content)
                        f.write("\n" + "="*50 + "\n\n")
                        
                    email_content = []
                continue
                
            line = data.decode('utf-8', errors='ignore').strip()
            if not line:
                continue
                
            cmd = line.split()[0].upper()
            if cmd in ["EHLO", "HELO"]:
                conn.sendall(b"250 Hello\r\n")
            elif cmd == "MAIL":
                conn.sendall(b"250 OK\r\n")
            elif cmd == "RCPT":
                conn.sendall(b"250 OK\r\n")
            elif cmd == "DATA":
                data_mode = True
                conn.sendall(b"354 Start input, end with <CRLF>.<CRLF>\r\n")
            elif cmd == "QUIT":
                conn.sendall(b"221 Bye\r\n")
                break
            else:
                conn.sendall(b"250 OK\r\n")
    except Exception as e:
        print(f"[MOCK SMTP ERROR] {e}")
    finally:
        conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", 1025))
        server.listen(5)
        print("Mock SMTP server listening on 127.0.0.1:1025...")
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr))
            t.daemon = True
            t.start()
    except Exception as e:
        print(f"[MOCK SMTP FAIL] Bound failed: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    main()
