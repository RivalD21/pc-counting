FROM node:18-alpine

WORKDIR /pc-fe
COPY package*.json ./
RUN npm install
COPY . .

EXPOSE 7077
CMD ["node", "index.js"]
