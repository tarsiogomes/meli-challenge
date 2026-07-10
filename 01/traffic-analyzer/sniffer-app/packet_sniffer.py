#!/usr/bin/env python3
import os
import sys
import argparse
import socket
import time
import psycopg2
from scapy.all import sniff, IP

PROTOCOL_MAP = {1: "ICMP", 6: "TCP", 17: "UDP"}
dns_cache = {}

# parametros de conexao com healthcheck
DB_HOST = os.environ.get("DB_HOST", "db")
DB_NAME = os.environ.get("DB_NAME", "sniffer_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASSWORD", "postgres")

def get_db_connection():
    
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                connect_timeout=3
            )
            return conn
        except psycopg2.OperationalError:
            retries -= 1
            time.sleep(2)
    return None

def init_db():
    
    conn = get_db_connection()
    if not conn:
        print("[-] Erro critico: A conexao com o banco de dados falhou.", file=sys.stderr)
        sys.exit(1)
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS packets (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    origem VARCHAR(50),
                    destino VARCHAR(50),
                    hostname_destino VARCHAR(255),
                    protocolo VARCHAR(10),
                    tamanho INT
                );
            """)
            conn.commit()
            print("[*] Estrutura do Banco de Dados validada com sucesso.")
    except Exception as e:
        print(f"[-] Erro ao inicializar tabela: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

def get_hostname(ip):
    if ip in dns_cache:
        return dns_cache[ip]
    try:
        socket.setdefaulttimeout(0.3)
        hostname = socket.gethostbyaddr(ip)[0]
        dns_cache[ip] = hostname
    except (socket.herror, socket.gaierror, socket.timeout):
        dns_cache[ip] = "N/A"
    return dns_cache[ip]

def process_packet(packet):
    if packet.haslayer(IP):
        ip_layer = packet[IP]
        
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
        proto_num = ip_layer.proto
        proto_name = PROTOCOL_MAP.get(proto_num, f"Outro ({proto_num})")
        packet_size = len(packet)
        dst_hostname = get_hostname(dst_ip)
        
        print(f"[+] Origem: {src_ip:<15} | Destino: {dst_ip:<15} ({dst_hostname:<20}) | Proto: {proto_name:<6} | Tamanho: {packet_size} bytes")
        
        # Insere o registro em tempo real no banco
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO packets (origem, destino, hostname_destino, protocolo, tamanho) VALUES (%s, %s, %s, %s, %s)",
                        (src_ip, dst_ip, dst_hostname, proto_name, packet_size)
                    )
                conn.commit()
            except Exception as e:
                print(f"[-] Erro ao salvar log no banco: {e}", file=sys.stderr)
            finally:
                conn.close()

def main():
    parser = argparse.ArgumentParser(description="Sniffer corporativo com persistencia em banco.")
    parser.add_argument("-i", "--interface", required=True, help="Interface de rede (ex: eth0).")
    args = parser.parse_args()
    
    init_db()
    print(f"[*] Escutando trafego na interface: {args.interface}...")
    
    try:
        sniff(iface=args.interface, prn=process_packet, store=False)
    except KeyboardInterrupt:
        print("\n[*] Encerrando sniffer.")

if __name__ == "__main__":
    main()