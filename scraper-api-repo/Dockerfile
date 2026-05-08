FROM node:18-slim
WORKDIR /app
COPY package*.json ./

# CONFIGURAÇÃO PARA PULAR O ERRO DE SSL
RUN npm config set strict-ssl false
RUN npm config set registry http://registry.npmjs.org/
RUN npm install

COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]