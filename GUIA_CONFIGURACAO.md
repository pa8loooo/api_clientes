# 📘 Guia de Configuração — Nginx, Docker e Wireshark

Este guia cobre tudo que você precisa fazer **após ter o código pronto**, desde subir o ambiente até analisar o tráfego de rede.

---

## 1. Pré-requisitos

Instale as ferramentas antes de começar:

- **Docker Desktop** (Windows/Mac) ou **Docker Engine** (Linux):  
  https://docs.docker.com/get-docker/   

- **Git**:  
  https://git-scm.com/downloads

- **Wireshark**:  
  https://www.wireshark.org/download.html

Verifique se estão instalados:

```bash
docker --version        # Docker version 24.x.x
docker compose version  # Docker Compose version v2.x.x
git --version           # git version 2.x.x
```

---

## 2. Estrutura de Arquivos Esperada

Antes de subir o Docker, certifique-se que seu projeto está assim:

```
projeto-docker/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── index.html
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

---

## 3. Subindo o Ambiente com Docker Compose

```bash
# Entre na pasta do projeto
cd projeto-docker

# Build das imagens e subir containers em background
docker compose up --build -d

# Acompanhar logs (aguarde a mensagem "Banco de dados inicializado")
docker compose logs -f api
```

Aguarde até ver no log:

```
api  | Banco de dados inicializado.
api  | * Running on all addresses (0.0.0.0)
```

Depois acesse: **http://localhost**

### Verificação rápida dos containers

```bash
docker compose ps
```

Todos devem estar com status `Up` ou `healthy`.

### Testando a API diretamente (curl)

```bash
# Listar clientes (deve retornar [])
curl http://localhost/api/users

# Criar um cliente
curl -X POST http://localhost/api/users \
  -H "Content-Type: application/json" \
  -d '{"nome":"João Teste","email":"joao@teste.com","telefone":"(11) 99999-0000"}'

# Listar novamente
curl http://localhost/api/users
```

---

## 4. Entendendo a Configuração do Nginx

O arquivo `nginx/nginx.conf` faz duas coisas principais:

### 4.1 Servir o Frontend estático

```nginx
location / {
    root   /usr/share/nginx/html;
    index  index.html;
    try_files $uri $uri/ /index.html;
}
```

- Qualquer requisição para `/` serve o `index.html` do frontend.
- O volume `./frontend:/usr/share/nginx/html` monta os arquivos HTML dentro do container.

### 4.2 Proxy Reverso para a API

```nginx
location /api/ {
    rewrite ^/api/(.*)$ /$1 break;
    proxy_pass http://api_backend;
    ...
}
```

- Toda requisição para `/api/alguma-coisa` é **redirecionada internamente** para `http://api:5000/alguma-coisa`.
- O prefixo `/api` é removido pelo `rewrite` antes de chegar ao Flask.
- O `upstream api_backend` aponta para o serviço `api` na porta `5000` (rede interna Docker).

### 4.3 Cabeçalhos Importantes

```nginx
proxy_set_header X-Real-IP       $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

Esses cabeçalhos garantem que o backend saiba o IP real do cliente, mesmo passando pelo proxy.

---

## 5. Como o Frontend se Conecta ao Backend

O frontend (`index.html`) usa um caminho relativo:

```javascript
const API = '/api';
```

Isso significa que, ao fazer `fetch('/api/users')`, o navegador envia para `http://localhost/api/users`, que o **Nginx intercepta e redireciona** internamente para o Flask em `http://api:5000/users`.

Nenhuma configuração extra é necessária — tudo passa pelo Nginx na porta 80.

### Fluxo completo de uma requisição

```
Navegador
  → GET http://localhost/api/users
  → Nginx :80 (recebe na location /api/)
  → Nginx faz rewrite: /users
  → proxy_pass http://api:5000/users
  → Flask retorna JSON
  → Nginx retorna ao navegador
```

---

## 6. Analisando o Tráfego com Wireshark

### 6.1 O que capturar?

O Wireshark captura pacotes de rede em interfaces físicas ou virtuais. Como o Docker usa uma bridge de rede interna, você pode capturar:

- Na interface **loopback** (`lo` ou `Loopback`): tráfego entre host e containers.
- Na interface de rede Docker Bridge (`docker0` no Linux).

### 6.2 Passo a Passo

#### Windows / Mac

1. Abra o **Wireshark**.
2. Selecione a interface **Adapter for loopback traffic capture** (no Windows) ou **lo0** (no Mac).
3. Inicie a captura clicando no ícone de tubarão 🦈 (ou pressione **Ctrl+E**).
4. No navegador, acesse `http://localhost` e faça algumas operações (cadastrar, listar, excluir).
5. Pare a captura (**Ctrl+E**).

#### Linux

```bash
# Capturar na interface loopback (porta 80)
sudo wireshark &

# Ou via terminal com tcpdump (alternativa)
sudo tcpdump -i lo -n port 80 -w captura.pcap
```

### 6.3 Filtros Úteis no Wireshark

Aplique no campo de filtro (barra verde/vermelha no topo):

```
# Apenas HTTP
http

# Tráfego na porta 80
tcp.port == 80

# Requisições POST (criação de clientes)
http.request.method == "POST"

# Requisições GET (listagem)
http.request.method == "GET"

# Respostas HTTP
http.response

# Filtro combinado: HTTP na porta 80
http and tcp.port == 80
```

### 6.4 Pacotes para Identificar e Documentar

Para o trabalho, identifique e anote **ao menos 3 pacotes** distintos:

| # | O que procurar | O que você vai ver |
|---|----------------|--------------------|
| 1 | **TCP Handshake** | Pacotes SYN → SYN-ACK → ACK entre cliente e Nginx |
| 2 | **Requisição HTTP GET /api/users** | Método, headers, URL |
| 3 | **Resposta HTTP 200 OK** | Status, Content-Type: application/json, corpo JSON |
| 4 | **Requisição HTTP POST /api/users** | Body JSON com nome/email |
| 5 | **Resposta HTTP 201 Created** | Confirmação de criação |

### 6.5 Como Fazer os Prints para o Trabalho

1. Clique no pacote de interesse na lista.
2. Observe os painéis abaixo:
   - **Painel do meio**: detalhes dos campos (expanda Ethernet, IP, TCP, HTTP).
   - **Painel inferior**: bytes brutos.
3. Tire o print da tela inteira mostrando os 3 painéis.
4. Anote: protocolo, IP origem/destino, porta, tipo de requisição.

### 6.6 Observações sobre Segurança (para o relatório)

- O tráfego capturado é **HTTP puro (não criptografado)**.
- Em produção, usaríamos **HTTPS (TLS)** e o Wireshark mostraria apenas pacotes cifrados — o que é o comportamento desejado.
- A comunicação interna entre containers (API ↔ MySQL) ocorre na rede Docker Bridge e **não** é visível na interface loopback do host.

---

## 7. Preenchendo o Documento do Trabalho

### Seção 1 — Arquitetura

Use o diagrama do `README.md` como base:

```
Navegador → Nginx :80 → API Flask :5000 → MySQL :3306
```

Descreva: o Nginx atua como ponto de entrada único, servindo o frontend estático e redirecionando chamadas `/api/*` para o backend Python via rede interna Docker.

### Seção 2 — Portas

| Serviço / Container | Porta Interna | Porta Externa (Host) | Finalidade |
|---------------------|---------------|----------------------|------------|
| Nginx (proxy reverso)| 80            | 80                   | Entrada HTTP pública |
| API Backend (Flask)  | 5000          | Não exposta          | Lógica de negócio / CRUD |
| MySQL                | 3306          | Não exposta          | Banco de dados relacional |
| Frontend             | —             | —                    | Servido pelo Nginx como estático |

### Seção 3 — Containers

**Nginx:**
- Imagem base: `nginx:1.25-alpine`
- Variáveis de ambiente: nenhuma
- Volumes: `./nginx/nginx.conf` → `/etc/nginx/nginx.conf` e `./frontend` → `/usr/share/nginx/html`
- Dependências: `api`

**API Backend:**
- Imagem base: `python:3.12-slim` (build local via Dockerfile)
- Variáveis de ambiente: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- Volumes: nenhum (código copiado na build)
- Dependências: `mysql` (com healthcheck)
- Rotas: `POST /users`, `GET /users`, `GET /users/<id>`, `PUT /users/<id>`, `DELETE /users/<id>`

**MySQL:**
- Imagem base: `mysql:8.0`
- `MYSQL_ROOT_PASSWORD`: rootpassword
- `MYSQL_DATABASE`: clientesdb
- `MYSQL_USER` / `PASSWORD`: appuser / apppassword
- Volume de dados: `mysql_data` (volume Docker gerenciado)
- Scripts de inicialização: nenhum (tabela criada pela API no startup)

**Frontend:**
- Sem container próprio — servido diretamente pelo Nginx como arquivos estáticos.

### Seção 4 — Fluxo de Comunicação

| # | Origem | Destino | Protocolo / Porta | Descrição |
|---|--------|---------|-------------------|-----------|
| 1 | Navegador | Nginx | HTTP :80 | Requisição do usuário |
| 2 | Nginx | API Backend | HTTP interno :5000 | Proxy pass para `/api/*` |
| 3 | API Backend | MySQL | TCP :3306 | Query SQL (INSERT/SELECT) |
| 4 | MySQL | API Backend | TCP :3306 | Retorno dos dados |
| 5 | API Backend | Nginx | HTTP interno :5000 | JSON de resposta |
| 6 | Nginx | Navegador | HTTP :80 | Resposta final ao usuário |

### Seção 5 — Configuração do Nginx

Cole o conteúdo de `nginx/nginx.conf` e explique:

- `events { worker_connections 1024; }` — define o máximo de conexões simultâneas por processo worker.
- `upstream api_backend { server api:5000; }` — declara o grupo de servidores backend; `api` é o nome do serviço no Docker Compose (DNS interno).
- `listen 80;` — Nginx escuta na porta 80 do container.
- `location / { root /usr/share/nginx/html; }` — serve arquivos estáticos do frontend.
- `location /api/ { rewrite ... proxy_pass ... }` — redireciona chamadas de API para o Flask removendo o prefixo `/api`.
- `proxy_set_header X-Real-IP` — repassa o IP real do cliente para o backend.

### Seção 6 — Wireshark

Preencha com os prints e a tabela de pacotes capturados (siga o passo 6.4 acima).

### Seção 7 — Repositório Git

Após subir o código:

```bash
cd projeto-docker
git init
git add .
git commit -m "feat: projeto docker inicial — API Python + MySQL + Nginx"
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
git push -u origin main
```

---

## 8. Troubleshooting Comum

### Container `api` reiniciando em loop

```bash
docker compose logs api
```

Geralmente é o MySQL ainda inicializando. Aguarde e o backend tentará novamente automaticamente (lógica de retry no `app.py`).

### Porta 80 já em uso

```bash
# Linux/Mac — veja o que usa a porta 80
sudo lsof -i :80

# Windows
netstat -ano | findstr :80
```

Pare o serviço conflitante (Apache, IIS, outro Docker, etc.).

### Erro de CORS

O backend já tem `flask-cors` configurado. Se persistir, verifique se as requisições do frontend estão usando `/api/...` (caminho relativo) e não `http://localhost:5000/...` diretamente.

### Resetar o banco de dados

```bash
docker compose down -v   # remove volumes
docker compose up --build
```
