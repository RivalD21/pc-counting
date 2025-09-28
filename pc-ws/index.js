const { WebSocketServer, WebSocket } = require("ws");

console.log("server start!");
const wss = new WebSocketServer({ port: 8080 });
const clients = new Set();

wss.on("connection", function connection(ws) {
  console.log("ws client connected!");
  clients.add(ws);

  ws.on("error", console.error);
  ws.on("message", function message(data) {
    broadcast(data);
  });
});

function broadcast(message) {
  clients.forEach(function each(client) {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message.toString());
    }
  });
}
