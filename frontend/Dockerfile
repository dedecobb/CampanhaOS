# syntax=docker/dockerfile:1

# Para o frontend, diferente do backend, não separamos "dev" de
# "produção" em estágios distintos aqui — o Vite dev server é só para
# desenvolvimento local (docker-compose). O build de produção real
# (`npm run build`) gera arquivos estáticos que seriam servidos por NGINX
# ou um serviço de hosting estático — isso é responsabilidade de um
# módulo futuro de deploy/infraestrutura de produção, não deste
# Dockerfile de desenvolvimento.

FROM node:22-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
