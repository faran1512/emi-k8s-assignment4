// Loan EMI Calculator - simple Express server with MongoDB storage
const express = require("express");
const { MongoClient } = require("mongodb");

const app = express();
const PORT = process.env.PORT || 3000;
const MONGO_URL = process.env.MONGO_URL || "mongodb://localhost:27017/emidb";
const POD_NAME = process.env.HOSTNAME || "unknown";

app.use(express.json());
app.use(express.static("public"));

let db = null;

// ---- EMI formula: P * r * (1+r)^n / ((1+r)^n - 1) ----
function computeEMI(principal, annualRate, months) {
  const r = annualRate / 12 / 100; // monthly interest rate
  const factor = Math.pow(1 + r, months);
  const emi = r === 0 ? principal / months : (principal * r * factor) / (factor - 1);
  const totalPayment = emi * months;
  return {
    emi: +emi.toFixed(2),
    totalPayment: +totalPayment.toFixed(2),
    totalInterest: +(totalPayment - principal).toFixed(2),
  };
}

// POST /api/emi  { principal, rate, months }
app.post("/api/emi", async (req, res) => {
  const p = Number(req.body.principal);
  const rate = Number(req.body.rate);
  const n = Number(req.body.months);

  // server-side validation: positive numbers only
  if (!(p > 0) || !(rate > 0) || !(n > 0)) {
    return res.status(400).json({ error: "All inputs must be positive numbers." });
  }

  const result = computeEMI(p, rate, n);
  const doc = {
    principal: p,
    rate: rate,
    months: n,
    emi: result.emi,
    servedBy: POD_NAME,
    createdAt: new Date(),
  };
  await db.collection("calculations").insertOne(doc);

  res.json({ ...result, servedBy: POD_NAME });
});

// GET /api/history - last 10 calculations, newest first
app.get("/api/history", async (req, res) => {
  const docs = await db
    .collection("calculations")
    .find({}, { projection: { _id: 0 } })
    .sort({ createdAt: -1 })
    .limit(10)
    .toArray();
  res.json(docs);
});

// GET /health - 200 only when MongoDB is reachable (used as readiness probe)
app.get("/health", async (req, res) => {
  try {
    await db.command({ ping: 1 });
    res.status(200).send("OK");
  } catch (e) {
    res.status(503).send("MongoDB not reachable");
  }
});

// Connect to MongoDB, then start listening
MongoClient.connect(MONGO_URL)
  .then((client) => {
    db = client.db(); // database name comes from the connection string
    app.listen(PORT, () => console.log(`EMI app listening on port ${PORT}`));
  })
  .catch((err) => {
    console.error("Failed to connect to MongoDB:", err);
    process.exit(1);
  });
