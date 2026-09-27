import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import worker, { traiterStripe, validerDemande, sourceProspect, signatureStripe, verifierSignatureStripe, champsPaiement } from "../index.js";

const ENV = { AIRTABLE_TOKEN: "pat_test", AIRTABLE_BASE_ID: "appTEST0000000000", STRIPE_WEBHOOK_SECRET: "whsec_test",
  ASSETS: { fetch: async () => new Response("page statique", { status: 200 }) } };
const MAINTENANT = new Date("2026-09-27T10:00:00Z");
let appels;

beforeEach(() => {
  appels = [];
  globalThis.fetch = async (url, options = {}) => {
    appels.push({ url: String(url), method: options.method || "GET", body: options.body ? JSON.parse(options.body) : null,
      auth: options.headers?.Authorization });
    if ((options.method || "GET") === "GET") {
      return new Response(JSON.stringify({ records: globalThis.__existants || [] }), { status: 200 });
    }
    return new Response(JSON.stringify({ records: [{ id: "recNOUVEAU0000000" }] }), { status: 200 });
  };
  globalThis.__existants = [];
});

const DEMANDE = { pays: "Israël", ville_parent: "Sarcelles", age_parent: "76",
  demarche: "Compte Ameli bloqué depuis deux mois", email: "Sarah@Exemple.co.il",
  creneau: "mardi 19 h heure d'Israël", _gotcha: "", gclid: "Cj0KCQ-abc_123" };

function requeteFormulaire(donnees) {
  const f = new FormData();
  for (const [k, v] of Object.entries(donnees)) f.append(k, v);
  return new Request("https://relais.test/api/demande", { method: "POST", body: f });
}

test("validation : demande complète acceptée, courriel normalisé", () => {
  const { demande, erreurs } = validerDemande(DEMANDE);
  assert.deepEqual(erreurs, []);
  assert.equal(demande.email, "sarah@exemple.co.il");
  assert.equal(demande.age, 76);
});

test("validation : champs manquants ou hors limites signalés", () => {
  const { erreurs } = validerDemande({ pays: "Mars", age_parent: "12", demarche: "court", email: "x" });
  assert.deepEqual(erreurs.sort(), ["age_parent", "creneau", "demarche", "email", "pays", "ville_parent"]);
});

test("source : gclid prioritaire, sinon repli sur utm_source", () => {
  assert.equal(sourceProspect({ gclid: "abc", source: "" }), "Google Ads");
  assert.equal(sourceProspect({ gclid: "", source: "facebook" }), "Communauté");
  assert.equal(sourceProspect({ gclid: "", source: "" }), "Site direct");
});

test("formulaire : crée la ligne Prospects avec les bons champs", async () => {
  const r = await worker.fetch(requeteFormulaire(DEMANDE), ENV);
  assert.equal(r.status, 200);
  assert.equal(appels.length, 1);
  const { url, method, body, auth } = appels[0];
  assert.equal(method, "POST");
  assert.equal(url, "https://api.airtable.com/v0/appTEST0000000000/Prospects");
  assert.equal(auth, "Bearer pat_test");
  const f = body.records[0].fields;
  assert.equal(f["Statut"], "Demande reçue");
  assert.equal(f["Enfant — Courriel"], "sarah@exemple.co.il");
  assert.equal(f["Parent — Âge"], 76);
  assert.equal(f["Source"], "Google Ads");
  assert.equal(f["gclid"], "Cj0KCQ-abc_123");
  assert.equal(body.typecast, true);
});

test("formulaire : le champ piège n'enregistre rien", async () => {
  const r = await worker.fetch(requeteFormulaire({ ...DEMANDE, _gotcha: "robot" }), ENV);
  assert.equal(r.status, 200);
  assert.equal(appels.length, 0);
});

test("formulaire : 400 si invalide, 503 sans configuration (bascule messagerie)", async () => {
  assert.equal((await worker.fetch(requeteFormulaire({ ...DEMANDE, email: "faux" }), ENV)).status, 400);
  assert.equal((await worker.fetch(requeteFormulaire(DEMANDE), { ASSETS: ENV.ASSETS })).status, 503);
  assert.equal(appels.length, 0);
});

test("formulaire : 502 si Airtable refuse", async () => {
  globalThis.fetch = async () => new Response("erreur", { status: 422 });
  assert.equal((await worker.fetch(requeteFormulaire(DEMANDE), ENV)).status, 502);
});

test("pages statiques servies par ASSETS, routes /api inconnues en 404, GET refusé", async () => {
  assert.equal(await (await worker.fetch(new Request("https://relais.test/cgv/"), ENV)).text(), "page statique");
  assert.equal((await worker.fetch(new Request("https://relais.test/api/autre", { method: "POST" }), ENV)).status, 404);
  assert.equal((await worker.fetch(new Request("https://relais.test/api/demande"), ENV)).status, 405);
});

// --- Stripe --------------------------------------------------------------
const SESSION = { id: "cs_test_1", object: "checkout.session", payment_status: "paid", amount_total: 5900,
  customer: "cus_1", subscription: "sub_1", metadata: { offre: "fondateur" },
  customer_details: { email: "SARAH@exemple.co.il", name: "Sarah Levi", phone: "+972500000000" },
  custom_fields: [{ key: "parent", type: "text", text: { value: "Mme Durand, Sarcelles" } },
    { key: "consentement", type: "dropdown", dropdown: { value: "cgvetexecutionanticipee" } }] };

async function requeteStripe(evenement, secret = "whsec_test", decalage = 0) {
  const corps = JSON.stringify(evenement);
  const t = Math.floor(MAINTENANT.getTime() / 1000) + decalage;
  const sig = await signatureStripe(secret, t, corps);
  return new Request("https://relais.test/api/stripe", { method: "POST", body: corps,
    headers: { "Stripe-Signature": `t=${t},v1=${sig}` } });
}

test("signature Stripe : valide, falsifiée, trop ancienne", async () => {
  const sig = await signatureStripe("whsec_test", 1000, "{}");
  assert.equal(await verifierSignatureStripe(`t=1000,v1=${sig}`, "{}", "whsec_test", 1000), true);
  assert.equal(await verifierSignatureStripe(`t=1000,v1=${sig}`, "{ }", "whsec_test", 1000), false);
  assert.equal(await verifierSignatureStripe(`t=1000,v1=${sig}`, "{}", "whsec_test", 2000), false);
  assert.equal(await verifierSignatureStripe(null, "{}", "whsec_test", 1000), false);
});

test("champs de paiement : montant, offre, identifiants, accord d'exécution anticipée", () => {
  const f = champsPaiement(SESSION, MAINTENANT);
  assert.equal(f["Montant payé"], 59);
  assert.equal(f["Offre choisie"], "Tarif fondateur 59 €/mois");
  assert.equal(f["Stripe — Abonnement"], "sub_1");
  assert.equal(f["Accord exécution anticipée"], true);
  assert.equal(f["Payé le"], "2026-09-27");
});

test("paiement : met à jour le prospect existant et passe au statut Payé", async () => {
  globalThis.__existants = [{ id: "recEXISTANT000000", fields: { "Statut": "Accord de principe", "Notes": "Appel du 25/09" } }];
  const r = await traiterStripe(await requeteStripe({ type: "checkout.session.completed", data: { object: SESSION } }), ENV, MAINTENANT);
  assert.equal(r.status, 200);
  assert.equal(appels.length, 2);
  assert.match(decodeURIComponent(appels[0].url), /LOWER\(\{Enfant — Courriel\}\)='sarah@exemple\.co\.il'/);
  const maj = appels[1];
  assert.equal(maj.method, "PATCH");
  const f = maj.body.records[0].fields;
  assert.equal(maj.body.records[0].id, "recEXISTANT000000");
  assert.equal(f["Statut"], "Payé");
  assert.equal(f["Enfant — Prénom Nom"], "Sarah Levi");
  assert.match(f["Notes"], /^Appel du 25\/09\n\[2026-09-27\] Paiement Stripe 59 €.*Mme Durand, Sarcelles/);
});

test("paiement : ne fait pas reculer un statut plus avancé", async () => {
  globalThis.__existants = [{ id: "recEXISTANT000000", fields: { "Statut": "Client actif" } }];
  await traiterStripe(await requeteStripe({ type: "checkout.session.completed", data: { object: { ...SESSION, metadata: { offre: "hospitalisation" }, amount_total: 49000 } } }), ENV, MAINTENANT);
  const f = appels[1].body.records[0].fields;
  assert.equal(f["Statut"], undefined);
  assert.equal(f["Offre choisie"], "Hospitalisation 490 €");
});

test("paiement sans prospect connu : création d'une ligne à vérifier", async () => {
  await traiterStripe(await requeteStripe({ type: "checkout.session.completed", data: { object: SESSION } }), ENV, MAINTENANT);
  const creation = appels[1];
  assert.equal(creation.method, "POST");
  const f = creation.body.records[0].fields;
  assert.equal(f["Statut"], "Payé");
  assert.equal(f["Enfant — Courriel"], "sarah@exemple.co.il");
  assert.match(f["Notes"], /vérifier le dossier/);
});

test("Stripe : signature invalide refusée, événements non concernés ignorés, 503 sans secret", async () => {
  const falsifiee = await requeteStripe({ type: "checkout.session.completed", data: { object: SESSION } }, "whsec_autre");
  assert.equal((await traiterStripe(falsifiee, ENV, MAINTENANT)).status, 400);
  const autre = await traiterStripe(await requeteStripe({ type: "invoice.paid", data: { object: {} } }), ENV, MAINTENANT);
  assert.equal(autre.status, 200);
  assert.equal(appels.length, 0);
  const sansSecret = await traiterStripe(await requeteStripe({ type: "x", data: {} }), { ...ENV, STRIPE_WEBHOOK_SECRET: "" }, MAINTENANT);
  assert.equal(sansSecret.status, 503);
});
