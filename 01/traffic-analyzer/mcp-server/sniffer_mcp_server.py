#!/usr/bin/env python3
import json
import sys
import subprocess

def query_database(sql_command):
    
    docker_cmd = [
        "docker", "exec", "sniffer_postgres", 
        "psql", "-U", "postgres", "-d", "sniffer_db", "-c", sql_command
    ]
    try:
        result = subprocess.run(docker_cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Erro ao executar consulta: {e.stderr}"
    except Exception as e:
        return f"Erro inesperado: {str(e)}"

def main():
    # Loop principal de comunicacao STDIO exigido pelo protocolo MCP
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line)
            
            # 1. Fase de Inicializacao/Handshake do MCP
            if request.get("method") == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "serverInfo": {"name": "sniffer-mcp-server", "version": "1.0.0"}
                    }
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                continue

            # 2. Tools MCP Server
            elif request.get("method") == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "consultar_trafego",
                                "description": "Consulta métricas de tráfego de rede capturadas pelo sniffer no banco PostgreSQL. Permite obter top conexões, pacotes UDP e últimos pacotes trafegados.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "tipo_analise": {
                                            "type": "string",
                                            "enum": ["top_udp", "top_conexoes", "top_geral", "ultimos_pacotes"],
                                            "description": "O tipo de relatório de rede desejado."
                                        }
                                    },
                                    "required": ["tipo_analise"]
                                }
                            }
                        ]
                    }
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                continue

            # 3. Selecao de Tool para execucao 
            elif request.get("method") == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                tipo = arguments.get("tipo_analise")
                
                sql = ""
                if tipo == "top_udp":
                    sql = "SELECT origem, destino, COUNT(*) as total_pacotes, SUM(tamanho) as total_bytes FROM packets WHERE protocolo = 'UDP' GROUP BY origem, destino ORDER BY total_pacotes DESC LIMIT 5;"
                elif tipo == "top_conexoes":
                    sql = "SELECT origem, destino, COUNT(*) as total_pacotes, SUM(tamanho) as total_bytes FROM packets GROUP BY origem, destino ORDER BY total_pacotes DESC LIMIT 5;"
                elif tipo == "top_geral":
                    sql = "SELECT origem, destino, protocolo, COUNT(*) as total_pacotes, SUM(tamanho) as total_bytes FROM packets GROUP BY origem, destino, protocolo ORDER BY total_pacotes DESC LIMIT 10;"
                elif tipo == "ultimos_pacotes":
                    sql = "SELECT * FROM packets ORDER BY id DESC LIMIT 10;"
                
                if sql:
                    output = query_database(sql)
                    content = [{"type": "text", "text": output}]
                else:
                    content = [{"type": "text", "text": "Tipo de análise inválido."}]

                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {"content": content, "isError": False}
                }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                continue

        except Exception as e:
            # Envia erro genérico estruturado para não quebrar o processo do Claude
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()