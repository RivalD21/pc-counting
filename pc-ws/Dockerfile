FROM node:18-alpine

WORKDIR /pc-ws
COPY package*.json ./
RUN npm install
COPY . .

EXPOSE 8080
CMD ["node", "index.js"]
