# 🐳 Cadastro de Clientes — Docker + Python + MySQL + Nginx

Projeto prático de infraestrutura moderna com containers Docker, API REST em Python (Flask), banco de dados MySQL, proxy reverso Nginx e análise de tráfego com Wireshark.

---

## 📁 Estrutura do Projeto

```
projeto-docker/
├── backend/
│   ├── app.py              # API Flask (CRUD de clientes)
│   ├── requirements.txt    # Dependências Python
│   └── Dockerfile          # Imagem do backend
├── frontend/
│   └── index.html          # Interface web (HTML + CSS + JS)
├── nginx/
│   └── nginx.conf          # Configuração do proxy reverso
├── docker-compose.yml      # Orquestração dos containers
└── README.md
```

---

## ⚡ Execução Rápida

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd projeto-docker

# 2. Suba todos os containers
docker compose up --build

# 3. Acesse no navegador
http://localhost
```

> O MySQL pode demorar ~15s para inicializar. O backend aguarda automaticamente.

---

## 🔌 Endpoints da API

| Método | Rota            | Descrição              |
|--------|-----------------|------------------------|
| GET    | `/api/users`    | Lista todos os clientes |
| POST   | `/api/users`    | Cria novo cliente      |
| GET    | `/api/users/:id`| Busca cliente por ID   |
| PUT    | `/api/users/:id`| Atualiza cliente       |
| DELETE | `/api/users/:id`| Remove cliente         |
| GET    | `/api/health`   | Verificação de saúde   |

### Exemplo POST `/api/users`

```bash
curl -X POST http://localhost/api/users \
  -H "Content-Type: application/json" \
  -d '{"nome": "Maria Silva", "email": "maria@email.com", "telefone": "(11) 91234-5678"}'
```

---

## 🗺️ Arquitetura

```
Navegador
    │  HTTP :80
    ▼
┌─────────┐
│  Nginx  │  (proxy reverso)
│ :80     │
└────┬────┘
     │ /api → http://api:5000
     │ /    → /usr/share/nginx/html (frontend estático)
     ▼
┌─────────┐       ┌─────────┐
│   API   │ ----->│  MySQL  │
│ Flask   │ :3306 │  :3306  │
│ :5000   │       │         │
└─────────┘       └─────────┘
```

---

## 🐋 Containers

| Container | Imagem            | Porta interna | Porta host | Função               |
|-----------|-------------------|---------------|------------|----------------------|
| nginx     | nginx:1.25-alpine | 80            | 8080       | Proxy reverso + front|
| api       | (build local)     | 5000          | —          | API REST Python      |
| mysql     | mysql:8.0         | 3306          | —          | Banco de dados       |

---

## 📋 Comandos Úteis

```bash
# Ver logs em tempo real
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f api

# Parar tudo
docker compose down

# Parar e remover volume do banco (reset total)
docker compose down -v

# Verificar containers rodando
docker compose ps

# Acessar shell do container da API
docker exec -it api bash

# Acessar MySQL diretamente
docker exec -it mysql mysql -u appuser -papppassword clientesdb
```

---

## 🛠️ Variáveis de Ambiente

Definidas no `docker-compose.yml`. Para produção, use um arquivo `.env`:

```env
DB_HOST=mysql
DB_PORT=3306
DB_USER=appuser
DB_PASSWORD=apppassword
DB_NAME=clientesdb
MYSQL_ROOT_PASSWORD=rootpassword
```

---

## 📌 Requisitos do Sistema

- Docker ≥ 24.x
- Docker Compose ≥ 2.x (plugin integrado)
- Porta 80 disponível no host
