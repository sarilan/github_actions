// Worker du site Relais (Cloudflare Workers, offre gratuite).
//
// - Sert les pages statiques du dossier dist/ (binding ASSETS).
// - POST /api/demande : reçoit le formulaire « Réserver un appel » et crée la ligne dans la
//   table Prospects d'Airtable. Sans configuration, répond 503 : la page bascule alors
//   d'elle-même sur l'envoi par messagerie, aucune demande n'est perdue.
// - POST /api/stripe : reçoit les notifications de paiement Stripe (checkout.session.completed),
//   vérifie leur signature et met le prospect correspondant au statut « Payé ».
//
// Réglages (Cloudflare → Workers & Pages → relais-parents → Paramètres → Variables et secrets) :
//   AIRTABLE_TOKEN          secret   jeton d'accès personnel Airtable (data.records:read et write sur la base Relais)
//   AIRTABLE_BASE_ID        variable identifiant de la base « Relais — Gestion » (déclaré dans wrangler.jsonc)
//   AIRTABLE_TABLE          variable nom de la table des prospects (par défaut « Prospects »)
//   STRIPE_WEBHOOK_SECRET   secret   secret de signature du point de terminaison Stripe (whsec_…)

export const PAYS = [
  "Israël", "Suisse", "Belgique", "Luxembourg", "Royaume-Uni", "États-Unis", "Canada",
  "Émirats arabes unis", "Singapour", "Hong Kong", "Autre pays",
];

export const OFFRES = {
  abonnement: "Abonnement 89 €/mois",
  fondateur: "Tarif fondateur 59 €/mois",
  diagnostic: "Diagnostic initial 149 €",
  hospitalisation: "Hospitalisation 490 €",
  ehpad: "EHPAD 690 €",
  succession: "Succession 890 €",
  demarche: "Démarche isolée 79 €",
};

// Statuts à partir desquels un paiement fait passer le prospect à « Payé ».
const STATUTS_AVANT_PAIEMENT = ["Demande reçue", "Appel fixé", "Appel fait", "Accord de principe"];

const COURRIEL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function json(corps, statut = 200) {
  return new Response(JSON.stringify(corps), {
    status: statut,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function texte(valeur, max) {
  return String(valeur ?? "").replace(/\s+/g, " ").trim().slice(0, max);
}

// ---------------------------------------------------------------------------
// Formulaire de demande d'appel
// ---------------------------------------------------------------------------
export function validerDemande(d) {
  const erreurs = [];
  const demande = {
    pays: texte(d.pays, 40),
    ville: texte(d.ville_parent, 80),
    age: Number(texte(d.age_parent, 3)),
    demarche: String(d.demarche ?? "").trim().slice(0, 1500),
    email: texte(d.email, 120).toLowerCase(),
    creneau: texte(d.creneau, 160),
    gclid: texte(d.gclid, 200).replace(/[^A-Za-z0-9_\-]/g, ""),
    source: texte(d.source, 60),
  };
  if (!PAYS.includes(demande.pays)) erreurs.push("pays");
  if (!demande.ville) erreurs.push("ville_parent");
  if (!Number.isInteger(demande.age) || demande.age < 50 || demande.age > 110) erreurs.push("age_parent");
  if (demande.demarche.length < 10) erreurs.push("demarche");
  if (!COURRIEL_RE.test(demande.email)) erreurs.push("email");
  if (!demande.creneau) erreurs.push("creneau");
  return { demande, erreurs };
}

export function sourceProspect(demande) {
  if (demande.gclid) return "Google Ads";
  const s = demande.source.toLowerCase();
  if (s.includes("google")) return "Google Ads";
  if (s.includes("facebook") || s.includes("whatsapp") || s.includes("communaute")) return "Communauté";
  if (s.includes("parrain") || s.includes("recommandation")) return "Recommandation";
  if (s.includes("prescripteur")) return "Prescripteur";
  return "Site direct";
}

async function lireCorps(request) {
  const type = request.headers.get("Content-Type") || "";
  if (type.includes("application/json")) return await request.json();
  const form = await request.formData();
  return Object.fromEntries(form.entries());
}

async function airtable(env, chemin, options = {}) {
  const table = encodeURIComponent(env.AIRTABLE_TABLE || "Prospects");
  const reponse = await fetch(`https://api.airtable.com/v0/${env.AIRTABLE_BASE_ID}/${table}${chemin}`, {
    ...options,
    headers: { Authorization: `Bearer ${env.AIRTABLE_TOKEN}`, "Content-Type": "application/json" },
  });
  if (!reponse.ok) {
    throw new Error(`Airtable ${reponse.status} : ${(await reponse.text()).slice(0, 300)}`);
  }
  return reponse.json();
}

export async function traiterDemande(request, env, maintenant = new Date()) {
  if (!env.AIRTABLE_TOKEN || !env.AIRTABLE_BASE_ID) return json({ ok: false, erreur: "configuration" }, 503);
  let donnees;
  try {
    donnees = await lireCorps(request);
  } catch {
    return json({ ok: false, erreur: "format" }, 400);
  }
  // Champ piège : un robot le remplit, un visiteur ne le voit pas. Réponse normale, rien n'est enregistré.
  if (texte(donnees._gotcha, 200)) return json({ ok: true });
  const { demande, erreurs } = validerDemande(donnees);
  if (erreurs.length) return json({ ok: false, erreur: "validation", champs: erreurs }, 400);

  const fields = {
    "Prospect": `${demande.ville} — ${demande.pays}`,
    "Statut": "Demande reçue",
    "Reçue le": maintenant.toISOString(),
    "Enfant — Courriel": demande.email,
    "Enfant — Pays": demande.pays,
    "Parent — Ville": demande.ville,
    "Parent — Âge": demande.age,
    "Démarche décrite": demande.demarche,
    "Créneau souhaité": demande.creneau,
    "Source": sourceProspect(demande),
  };
  if (demande.gclid) fields["gclid"] = demande.gclid;
  try {
    await airtable(env, "", { method: "POST", body: JSON.stringify({ records: [{ fields }], typecast: true }) });
  } catch (e) {
    console.error(String(e));
    return json({ ok: false, erreur: "enregistrement" }, 502);
  }
  return json({ ok: true });
}

// ---------------------------------------------------------------------------
// Notifications Stripe
// ---------------------------------------------------------------------------
function hex(buffer) {
  return [...new Uint8Array(buffer)].map((o) => o.toString(16).padStart(2, "0")).join("");
}

function egaliteConstante(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function signatureStripe(secret, horodatage, corps) {
  const cle = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", cle, new TextEncoder().encode(`${horodatage}.${corps}`)));
}

export async function verifierSignatureStripe(entete, corps, secret, maintenantSecondes, tolerance = 300) {
  if (!entete || !secret) return false;
  const parties = entete.split(",").map((p) => p.split("="));
  const t = parties.find(([k]) => k === "t")?.[1];
  const signatures = parties.filter(([k]) => k === "v1").map(([, v]) => v);
  if (!t || !signatures.length) return false;
  if (Math.abs(maintenantSecondes - Number(t)) > tolerance) return false;
  const attendue = await signatureStripe(secret, t, corps);
  return signatures.some((s) => egaliteConstante(s, attendue));
}

function champPersonnalise(session, cle) {
  const champ = (session.custom_fields || []).find((c) => c.key === cle);
  if (!champ) return "";
  return champ.text?.value || champ.dropdown?.value || champ.numeric?.value || "";
}

export function champsPaiement(session, maintenant) {
  const offre = session.metadata?.offre;
  const fields = {
    "Payé le": maintenant.toISOString().slice(0, 10),
    "Montant payé": (session.amount_total ?? 0) / 100,
    "Dernier contact": maintenant.toISOString().slice(0, 10),
  };
  if (OFFRES[offre]) fields["Offre choisie"] = OFFRES[offre];
  if (session.customer) fields["Stripe — Client"] = String(session.customer);
  if (session.subscription) fields["Stripe — Abonnement"] = String(session.subscription);
  if (champPersonnalise(session, "consentement")) fields["Accord exécution anticipée"] = true;
  return fields;
}

export async function traiterStripe(request, env, maintenant = new Date()) {
  if (!env.STRIPE_WEBHOOK_SECRET || !env.AIRTABLE_TOKEN || !env.AIRTABLE_BASE_ID) {
    return json({ ok: false, erreur: "configuration" }, 503);
  }
  const corps = await request.text();
  const valide = await verifierSignatureStripe(request.headers.get("Stripe-Signature"), corps,
    env.STRIPE_WEBHOOK_SECRET, Math.floor(maintenant.getTime() / 1000));
  if (!valide) return json({ ok: false, erreur: "signature" }, 400);

  const evenement = JSON.parse(corps);
  if (evenement.type !== "checkout.session.completed") return json({ ok: true, ignore: evenement.type });
  const session = evenement.data.object;
  if (session.payment_status !== "paid" && session.payment_status !== "no_payment_required") {
    return json({ ok: true, ignore: "paiement non abouti" });
  }

  const email = String(session.customer_details?.email || "").toLowerCase();
  const nom = texte(session.customer_details?.name, 80);
  const parent = texte(champPersonnalise(session, "parent"), 120);
  const fields = champsPaiement(session, maintenant);
  const note = `[${maintenant.toISOString().slice(0, 10)}] Paiement Stripe ${fields["Montant payé"]} € (${session.id})`
    + (parent ? ` — parent indiqué : ${parent}` : "");

  try {
    let existant = null;
    if (email) {
      const formule = `LOWER({Enfant — Courriel})='${email.replace(/\\/g, "\\\\").replace(/'/g, "\\'")}'`;
      const resultat = await airtable(env, `?maxRecords=1&filterByFormula=${encodeURIComponent(formule)}`
        + `&sort%5B0%5D%5Bfield%5D=${encodeURIComponent("Reçue le")}&sort%5B0%5D%5Bdirection%5D=desc`);
      existant = resultat.records?.[0] || null;
    }
    if (existant) {
      const statut = existant.fields?.["Statut"];
      if (!statut || STATUTS_AVANT_PAIEMENT.includes(statut)) fields["Statut"] = "Payé";
      if (nom && !existant.fields?.["Enfant — Prénom Nom"]) fields["Enfant — Prénom Nom"] = nom;
      fields["Notes"] = [existant.fields?.["Notes"], note].filter(Boolean).join("\n");
      await airtable(env, "", { method: "PATCH", body: JSON.stringify({ records: [{ id: existant.id, fields }], typecast: true }) });
    } else {
      Object.assign(fields, {
        "Prospect": nom || email || session.id,
        "Statut": "Payé",
        "Reçue le": maintenant.toISOString(),
        "Enfant — Prénom Nom": nom,
        "Enfant — Courriel": email || undefined,
        "Enfant — Téléphone": session.customer_details?.phone || undefined,
        "Source": "Autre",
        "Notes": `${note}\nPaiement reçu sans demande préalable dans la table : vérifier le dossier.`,
      });
      await airtable(env, "", { method: "POST", body: JSON.stringify({ records: [{ fields }], typecast: true }) });
    }
  } catch (e) {
    console.error(String(e));
    // 500 : Stripe renvoie la notification plus tard, rien n'est perdu.
    return json({ ok: false, erreur: "enregistrement" }, 500);
  }
  return json({ ok: true });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/demande") {
      return request.method === "POST" ? traiterDemande(request, env) : json({ ok: false }, 405);
    }
    if (url.pathname === "/api/stripe") {
      return request.method === "POST" ? traiterStripe(request, env) : json({ ok: false }, 405);
    }
    if (url.pathname.startsWith("/api/")) return json({ ok: false }, 404);
    return env.ASSETS.fetch(request);
  },
};
