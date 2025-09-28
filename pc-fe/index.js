const express = require('express');
const app = express();
const path = require('path');
const port = 7077;

app.use(express.static('dist'));

// Fallback untuk semua rute
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(port, () => {
  console.log(`Example app listening at ${port}`);
});
