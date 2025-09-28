const express = require("express");
const app = express();
const port = 3000;
const cors = require("cors");
const MYSQLcon = require("./database");

//-------------------------------------------------------------------------
// load body-parser
const bodyParser = require("body-parser");
app.use("/assets", express.static("assets/"));
app.use(cors());

//-------------------------------------------------------------------------
// parse permintaan express - application / json
app.use(express.json());
// parse permintaan jenis konten - application / json
app.use(bodyParser.json());
// parse permintaan jenis konten - application / x-www-form-urlencoded
app.use(bodyParser.urlencoded({ extended: true }));

// Error handling mideelware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send("Something broke!");
});

app.get("/", (req, res) => res.send("STATUS API READY TO USE"));
app.get("/api/areas", (req, res) => {
  MYSQLcon.query("SELECT * FROM areas", function (err, result, fields) {
    if (err) {
      res.send("error select : " + err);
    } else {
      res.json(result);
    }
  });
});
app.get("/api/areas/:id", (req, res) => {
  MYSQLcon.query(
    "SELECT * FROM areas WHERE area_id = " + req.params.id + "",
    function (err, result, fields) {
      if (err) {
        res.send("error select : " + err);
      } else {
        res.json(result);
      }
    }
  );
});

app.put("/api/areas/:id", (req, res) => {
  const { area_nama, deskripsi, polygon, is_active, timestamp } = req.body;
  MYSQLcon.query(
    "UPDATE areas SET area_nama = '" +
      area_nama +
      "', deskripsi = '" +
      deskripsi +
      "' polygon = '" +
      polygon +
      "', is_active = '" +
      is_active +
      "', timestamp = '" +
      timestamp +
      "' WHERE area_id =  " +
      req.params.id +
      "",
    function (err, result, fields) {
      if (err) {
        res.send("error select : " + err);
      } else {
        res.json(result);
      }
    }
  );
});

app.get("/api/config", (req, res) => {
  MYSQLcon.query(
    "SELECT cameras.source_url, areas.polygon FROM cameras INNER JOIN areas ON cameras.camera_id = areas.camera_id",
    function (err, result, fields) {
      if (err) {
        res.send("error select : " + err);
      } else {
        res.json(result);
      }
    }
  );
});

app.get("/api/cameras", (req, res) => {
  MYSQLcon.query("SELECT * FROM cameras", function (err, result, fields) {
    if (err) {
      res.send("error select : " + err);
    } else {
      res.json(result);
    }
  });
});

app.get("/api/cameras/:id", (req, res) => {
  MYSQLcon.query(
    "SELECT * FROM cameras WHERE camera_id = " + req.params.id + "",
    function (err, result, fields) {
      if (err) {
        res.send("error select : " + err);
      } else {
        res.json(result);
      }
    }
  );
});

app.put("/api/cameras/:id", (req, res) => {
  const { name, source_url, location_note } = req.body;
  MYSQLcon.query(
    "UPDATE cameras SET name = '" +
      name +
      "', source_url = '" +
      source_url +
      "' location_note = '" +
      location_note +
      "' WHERE camera_id =  " +
      req.params.id +
      "",
    function (err, result, fields) {
      if (err) {
        res.send("error select : " + err);
      } else {
        res.json(result);
      }
    }
  );
});

app.put("/api/polygon/:id", (req, res) => {
  const { polygon } = req.body;
  MYSQLcon.query(
    "UPDATE areas SET polygon = ? WHERE area_id = ?",
    [JSON.stringify(polygon), req.params.id],
    function (err, result, fields) {
      if (err) {
        res.send("error select : " + err);
      } else {
        res.json(result);
      }
    }
  );
});

app.get("/api/ws", (req, res) => {
  MYSQLcon.query("SELECT * FROM setting", function (err, result, fields) {
    if (err) {
      res.send("error select : " + err);
    } else {
      res.json(result);
    }
  });
});

app.put("/api/ws/:id", (req, res) => {
  const { wsUrl } = req.body;

  MYSQLcon.query(
    "UPDATE setting SET websocket = ? WHERE setting_id = ?",
    [wsUrl, req.params.id],
    function (err, result, fields) {
      if (err) {
        res.send("error select : " + err);
      } else {
        res.json(result);
      }
    }
  );
});

app.get("/api/stats", (req, res) => {
  const { from, to, limit } = req.query;

  if (from && to) {
    const sql =
      "SELECT * FROM counting WHERE timestamp BETWEEN ? AND ? LIMIT " + limit;
    MYSQLcon.query(sql, [from, to], (err, result, fields) => {
      if (err) {
        res.status(500).send("error select : " + err);
      } else {
        res.json(result);
      }
    });
  } else {
    const sql = "SELECT * FROM counting LIMIT " + limit;
    MYSQLcon.query(sql, (err, result, fields) => {
      if (err) {
        res.status(500).send("error select : " + err);
      } else {
        res.json(result);
      }
    });
  }
});

app.get("/api/stats/live", (req, res) => {
  MYSQLcon.query(
    "SELECT * FROM counting ORDER BY counting_id DESC LIMIT 1;",
    function (err, result, fields) {
      if (err) {
        res.send("error select : " + err);
      } else {
        res.json(result);
      }
    }
  );
});

app.post("/api/counting", (req, res) => {
  const { camera_id, masuk, keluar, dalam } = req.body;

  MYSQLcon.query(
    "INSERT INTO counting (camera_id, masuk, keluar, dalam) VALUES ('" +
      camera_id +
      "', '" +
      masuk +
      "', '" +
      keluar +
      "', '" +
      dalam +
      "') ",
    function (err, result, fields) {
      if (err) {
        res.send("error select : " + err);
      } else {
        res.json(result);
      }
    }
  );
});

app.put("/api/counting_agg/:id", (req, res) => {
  const { masuk, keluar, dalam, timestamp } = req.body;
  MYSQLcon.query(
    "UPDATE counting_agg (masuk, keluar, dalam, timestamp) VALUES ('" +
      masuk +
      "', '" +
      keluar +
      "', '" +
      dalam +
      "', '" +
      timestamp +
      "') ",
    function (err, result, fields) {
      if (err) {
        res.send("error select : " + err);
      } else {
        res.json(result);
      }
    }
  );
});

app.listen(port, () => console.log(`app listening on port ${port}!`));
