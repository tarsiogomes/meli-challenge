# Analisador de Trafego de Rede com Integração MCP

>Este projeto consiste numa solução em microsserviços conteinerizada para captura, persistência e análise estatística de pacotes de rede (Camadas 3 e 4). O diferencial arquitetural baseia-se na exposição de dados por meio do **Model Context Protocol (MCP)**, permitindo auditorias e consultas complexas na infraestrutura utilizando linguagem natural via Claude Desktop.

---

## 1. Estrutura de Arquivos do Projeto

>Estrutura da aplicacao:
```
traffic-analyzer/
│
├── docker-compose.yml
│
├── sniffer-app/
│   ├── Dockerfile
│   └── packet_sniffer.py
│
└── mcp-server/
    ├── Dockerfile
    └── sniffer_mcp_server.py
```

## 2. Provisionamento da aplicacao em ambiente controlado para a PoC

### 2.1 Requisitos na estação de trabalho:

Docker version 29.6.1<br />
Python 3.13.14

### 2.2 Provisionar recursos:

> Execute o comando no terminal (Powershell)
```
docker compose up -d --build
```
> Verifique se os containers estao em execucao:
```
docker compose ps
```
> Saida esperada do comando:

<img width="1766" height="79" alt="image" src="https://github.com/user-attachments/assets/caa8c5cf-ee11-467b-bf8f-30e20184b81b" />

> Dados armazenados no volume "traffic-analyzer_postgres_data", para consultar execute:
```
docker volume ls
```
> A coleta do trafego foi direcionada para interfaces dos containers Docker como exemplo. Para realizar consultas manuais do trafego execute os comandos abaixo:
```
docker exec -it sniffer_postgres psql -U postgres -d sniffer_db -c "SELECT * FROM packets ORDER BY id DESC LIMIT 10;"
```
> Saida esperada do comando:

<img width="1111" height="260" alt="image" src="https://github.com/user-attachments/assets/d822b82e-68cb-4c43-b353-e0ace03ecbe3" />

> Comandos para realizar outras consultas:
```
docker exec -it sniffer_postgres psql -U postgres -d sniffer_db -c "SELECT origem, destino, protocolo, COUNT(*) as total_pacotes, SUM(tamanho) as total_bytes FROM packets GROUP BY origem, destino, protocolo ORDER BY total_pacotes DESC LIMIT 10;"
```
```
docker exec -it sniffer_postgres psql -U postgres -d sniffer_db -c "SELECT origem, destino, COUNT(*) as total_pacotes, SUM(tamanho) as total_bytes FROM packets GROUP BY origem, destino ORDER BY total_pacotes DESC LIMIT 5;"
```

## 3. Configuração do MCP Server no Claude Desktop

>O Claude Desktop interage com o MCP Server com LLM com a aplicacao sniffer_mcp.

PATH arquivo de Configuração:
>Para Windows: Pressione as teclas WinKey + R para iniciar o Executar e copie o comando abaixo e cole no Executar:
```
%APPDATA%\Claude\claude_desktop_config.json
```
>Para o macOS: Pressione command + Space e cole o comando abaixo para editar o arquivo de configuracao .json: 
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

>Adicione o trecho de código abaixo no arquivo .json do Claude Desktop, na lista de mcpServers:

```
"mcpServers": {
    "network-sniffer": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "//var/run/docker.sock:/var/run/docker.sock",
        "traffic-analyzer-mcp"
      ]
    }
  }
```
> Reinicie o aplicativo Claude caos esteja em execução e verifique em Conectores se está Habilitado:

<img width="876" height="523" alt="image" src="https://github.com/user-attachments/assets/761b065d-f2ed-470e-b32d-b2acd30e7b8c" />

>Exemplos de prompts no Claude Desktop:<br /><br />

"Quais são as 5 conexões com mais pacotes trafegados?"<br />
"Mostre o top 5 de tráfego de pacotes TCP."<br />
"Me traga uma lista dos últimos 10 pacotes capturados."<br />
"Quais são os 10 maiores fluxos de rede por protocolo?"<br />
"O sniffer registrou alguma atividade recente agora?"<br />
"Quem são os maiores geradores de tráfego UDP na rede?"<br />

> Permita a execução e realize a consulta:<br />

<img width="967" height="620" alt="image" src="https://github.com/user-attachments/assets/ff1ccb8f-394c-4ee8-a649-d8839116c735" />
<img width="934" height="614" alt="image" src="https://github.com/user-attachments/assets/3907bfe2-aa68-4137-bb19-74eff67d1b63" />

## 4. Nota de Isenção de Segurança (Ambiente Não Produtivo)

Este projeto foi concebido estritamente como uma Prova de Conceito (PoC) para ambientes de laboratório isolados. Visando a simplicidade e agilidade nas validacoes, todos os controles de segurança devem ser completamente revistos em cenários reais de produção.
