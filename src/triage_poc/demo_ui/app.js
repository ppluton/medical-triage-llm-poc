const copy = {
  fr: {
    intro: "Cette interface illustre une chaîne gouvernée : collecte, anonymisation, modèle, garde-fous et audit. Elle ne produit ni diagnostic ni décision médicale autonome.",
    intakeTitle: "Informations disponibles", ageGroup: "Groupe d’âge", adult: "Adulte",
    pediatric: "Pédiatrique", olderAdult: "Personne âgée", unknown: "Inconnu",
    duration: "Durée", symptoms: "Symptômes observés", listHelp: "Une information par ligne.",
    evolution: "Évolution", intensity: "Intensité", details: "Ajouter les éléments disponibles",
    associated: "Signes associés", history: "Antécédents pertinents", vulnerability: "Facteurs de vulnérabilité",
    accessToken: "Jeton d’accès à la démonstration", tokenHelp: "Utilisé pour cet appel uniquement. Il n’est pas enregistré.",
    assess: "Lancer l’évaluation encadrée", resultTitle: "Évaluation proposée", waiting: "En attente",
    empty: "Sélectionnez un scénario ou saisissez un contexte synthétique, puis lancez l’évaluation.",
    priority: "Priorité proposée", considered: "Éléments considérés", questions: "Informations à compléter",
    redFlags: "Signaux d’alerte relevés", latency: "Latence API", interaction: "Interaction", model: "Version modèle",
    running: "Évaluation en cours", warming: "Réveil du modèle · jusqu’à 2 min", ready: "Réponse contrôlée", error: "Échec explicite",
    required: "Renseignez au moins un symptôme synthétique et un jeton d’au moins 32 caractères.",
    unavailable: "L’évaluation est indisponible. Vérifiez le jeton ou consultez le journal technique expurgé.",
    guidedLabel: "Conversation guidée", guidedTitle: "Compléter sans recommencer",
    reassess: "Ajouter les réponses et réévaluer", unavailableAnswer: "Information indisponible",
    absentAnswer: "Aucun élément", answerRequired: "Répondez, indiquez une absence ou marquez l’information indisponible.",
  },
  en: {
    intro: "This interface demonstrates a governed chain: collection, anonymization, model, guardrails and audit. It provides neither diagnosis nor autonomous medical decisions.",
    intakeTitle: "Available information", ageGroup: "Age group", adult: "Adult",
    pediatric: "Pediatric", olderAdult: "Older adult", unknown: "Unknown",
    duration: "Duration", symptoms: "Observed symptoms", listHelp: "One item per line.",
    evolution: "Evolution", intensity: "Intensity", details: "Add available details",
    associated: "Associated signs", history: "Relevant history", vulnerability: "Vulnerability factors",
    accessToken: "Demonstration access token", tokenHelp: "Used for this request only. It is not stored.",
    assess: "Run governed assessment", resultTitle: "Proposed assessment", waiting: "Waiting",
    empty: "Select a scenario or enter a synthetic context, then run the assessment.",
    priority: "Proposed priority", considered: "Elements considered", questions: "Information to complete",
    redFlags: "Warning signs identified", latency: "API latency", interaction: "Interaction", model: "Model version",
    running: "Assessment running", warming: "Waking model · up to 2 min", ready: "Controlled response", error: "Explicit failure",
    required: "Enter at least one synthetic symptom and a token of at least 32 characters.",
    unavailable: "Assessment unavailable. Check the token or inspect the redacted technical log.",
    guidedLabel: "Guided conversation", guidedTitle: "Complete without starting over",
    reassess: "Add answers and reassess", unavailableAnswer: "Information unavailable",
    absentAnswer: "None", answerRequired: "Answer, confirm none, or mark the information unavailable.",
  },
};

const presets = {
  chest: {
    language: "fr", age: "adult", symptoms: ["douleur thoracique soudaine", "essoufflement"],
    duration: "depuis vingt minutes", evolution: "apparition brutale", intensity: "forte",
    associated: [], history: [], vulnerability: [], vitals: {},
  },
  stroke: {
    language: "en", age: "adult", symptoms: ["sudden weakness of the right arm", "difficulty speaking"],
    duration: "for ten minutes", evolution: "sudden onset", intensity: "marked",
    associated: [], history: [], vulnerability: [], vitals: {},
  },
};

let language = "fr";
let currentContext = null;
let pendingQuestions = [];
const byId = (id) => document.getElementById(id);
const asList = (value) => value.split(/\n|,/).map((item) => item.trim()).filter(Boolean);
const optionalNumber = (id) => byId(id).value === "" ? undefined : Number(byId(id).value);

function setLanguage(next) {
  language = next;
  document.documentElement.lang = next;
  document.querySelectorAll("[data-language]").forEach((button) => button.classList.toggle("active", button.dataset.language === next));
  document.querySelectorAll("[data-i18n]").forEach((node) => { node.textContent = copy[next][node.dataset.i18n]; });
}

function applyPreset(name) {
  const preset = presets[name];
  setLanguage(preset.language);
  byId("age-group").value = preset.age;
  byId("symptoms").value = preset.symptoms.join("\n");
  byId("duration").value = preset.duration;
  byId("evolution").value = preset.evolution;
  byId("intensity").value = preset.intensity;
  byId("associated").value = preset.associated.join("\n");
  byId("history").value = preset.history.join("\n");
  byId("vulnerability").value = preset.vulnerability.join("\n");
  ["heart-rate", "spo2", "temperature"].forEach((id) => { byId(id).value = ""; });
  document.querySelectorAll("[data-preset]").forEach((button) => button.classList.toggle("active", button.dataset.preset === name));
}

function renderList(id, values, fallback) {
  const list = byId(id);
  list.replaceChildren();
  const rows = values.length ? values : [fallback];
  rows.forEach((value) => { const item = document.createElement("li"); item.textContent = value; list.append(item); });
}

function renderResult(data) {
  byId("empty-result").hidden = true;
  byId("result").hidden = false;
  const priority = byId("priority");
  priority.className = `priority ${data.triage_level}`;
  byId("priority-value").textContent = data.triage_level;
  byId("summary").textContent = data.summary;
  renderList("rationale", data.clinical_rationale, language === "fr" ? "Aucun élément retourné." : "No element returned.");
  renderList("questions", data.follow_up_questions.length ? data.follow_up_questions : data.missing_information, language === "fr" ? "Aucune question complémentaire." : "No additional question.");
  const redFlags = data.red_flags || [];
  byId("red-flags-section").hidden = redFlags.length === 0;
  renderList("red-flags", redFlags, "");
  byId("latency").textContent = `${data.latency_ms.toFixed(0)} ms`;
  byId("interaction").textContent = data.interaction_id;
  byId("interaction").title = data.interaction_id;
  byId("model").textContent = data.model_version.slice(0, 12);
  byId("model").title = data.model_version;
  byId("safety").textContent = data.safety_notice;
  renderGuidedQuestions(data.collection.questions || []);
}

const listFields = new Set(["associated_symptoms", "medical_history", "allergies", "medications", "vulnerability_factors"]);

function buildAnswerInput(field) {
  if (field === "age_group") {
    const select = document.createElement("select");
    [["", "—"], ["pediatric", copy[language].pediatric], ["adult", copy[language].adult], ["older_adult", copy[language].olderAdult]].forEach(([value, label]) => {
      const option = document.createElement("option"); option.value = value; option.textContent = label; select.append(option);
    });
    return select;
  }
  if (field === "vitals") {
    const wrapper = document.createElement("div"); wrapper.className = "vitals";
    [["heart_rate", "FC", "bpm"], ["spo2", "SpO₂", "%"], ["temperature_c", "Temp.", "°C"]].forEach(([name, label, unit]) => {
      const item = document.createElement("label");
      const title = document.createElement("span"); title.textContent = label;
      const input = document.createElement("input"); input.type = "number"; input.dataset.vital = name; input.inputMode = "decimal";
      const suffix = document.createElement("small"); suffix.textContent = unit;
      item.append(title, input, suffix); wrapper.append(item);
    });
    return wrapper;
  }
  const input = listFields.has(field) ? document.createElement("textarea") : document.createElement("input");
  input.dataset.answer = field;
  input.maxLength = 2000;
  if (input.tagName === "TEXTAREA") input.rows = 2;
  return input;
}

function renderGuidedQuestions(questions) {
  pendingQuestions = questions;
  const form = byId("follow-up-form");
  const container = byId("guided-questions");
  container.replaceChildren();
  form.hidden = questions.length === 0;
  questions.forEach((question) => {
    const card = document.createElement("div"); card.className = "guided-question"; card.dataset.field = question.field;
    const label = document.createElement("label");
    const text = document.createElement("span"); text.textContent = question.text;
    label.append(text, buildAnswerInput(question.field)); card.append(label);
    if (question.field !== "age_group") {
      const actions = document.createElement("div"); actions.className = "guided-actions";
      if (listFields.has(question.field)) actions.append(buildStatusChoice(question.field, "absent", copy[language].absentAnswer));
      actions.append(buildStatusChoice(question.field, "unavailable", copy[language].unavailableAnswer));
      card.append(actions);
    }
    container.append(card);
  });
}

function buildStatusChoice(field, status, labelText) {
  const label = document.createElement("label");
  const input = document.createElement("input"); input.type = "radio"; input.name = `status-${field}`; input.value = status;
  const text = document.createElement("span"); text.textContent = labelText;
  label.append(input, text); return label;
}

function clearFieldStatus(context, field) {
  context.confirmed_absent = (context.confirmed_absent || []).filter((value) => value !== field);
  context.unavailable_fields = (context.unavailable_fields || []).filter((value) => value !== field);
}

function applyGuidedAnswers() {
  const next = structuredClone(currentContext);
  for (const question of pendingQuestions) {
    const card = document.querySelector(`.guided-question[data-field="${question.field}"]`);
    const selected = card.querySelector("input[type=radio]:checked")?.value;
    clearFieldStatus(next, question.field);
    if (selected === "unavailable") { next.unavailable_fields.push(question.field); continue; }
    if (selected === "absent") { next.confirmed_absent.push(question.field); continue; }
    if (question.field === "vitals") {
      const values = {};
      card.querySelectorAll("[data-vital]").forEach((input) => { if (input.value !== "") values[input.dataset.vital] = Number(input.value); });
      if (Object.keys(values).length === 0) throw new Error("answer_required");
      next.vitals = { ...(next.vitals || {}), ...values };
    } else {
      const input = card.querySelector("select, [data-answer]");
      if (!input.value.trim()) throw new Error("answer_required");
      next[question.field] = listFields.has(question.field) ? asList(input.value) : input.value.trim();
    }
  }
  return next;
}

document.querySelectorAll("[data-language]").forEach((button) => button.addEventListener("click", () => setLanguage(button.dataset.language)));
document.querySelectorAll("[data-preset]").forEach((button) => button.addEventListener("click", () => applyPreset(button.dataset.preset)));

async function assess(context, errorElement, submit) {
  const token = byId("token").value;
  errorElement.hidden = true;
  submit.disabled = true;
  byId("status").className = "status";
  byId("status").textContent = copy[language].running;
  try {
    const readyDeadline = Date.now() + 130000;
    while (true) {
      const health = await fetch("/v1/healthz", {
        headers: { "Authorization": `Bearer ${token}` },
      });
      if (health.ok) break;
      if (![502, 503].includes(health.status) || Date.now() >= readyDeadline) {
        throw new Error(`HTTP ${health.status}`);
      }
      byId("status").textContent = copy[language].warming;
      await new Promise((resolve) => setTimeout(resolve, 5000));
    }
    byId("status").textContent = copy[language].running;
    const response = await fetch("/v1/triage", {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ language, patient_context: context }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    currentContext = context;
    renderResult(await response.json());
    byId("status").className = "status ready";
    byId("status").textContent = copy[language].ready;
  } catch (_) {
    errorElement.textContent = copy[language].unavailable;
    errorElement.hidden = false;
    byId("status").className = "status error";
    byId("status").textContent = copy[language].error;
  } finally {
    submit.disabled = false;
  }
}

byId("triage-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const token = byId("token").value;
  const symptoms = asList(byId("symptoms").value);
  const error = byId("form-error");
  if (symptoms.length === 0 || token.length < 32) {
    error.textContent = copy[language].required; error.hidden = false; return;
  }
  error.hidden = true;
  const vitals = {};
  const heartRate = optionalNumber("heart-rate");
  const spo2 = optionalNumber("spo2");
  const temperature = optionalNumber("temperature");
  if (heartRate !== undefined) vitals.heart_rate = heartRate;
  if (spo2 !== undefined) vitals.spo2 = spo2;
  if (temperature !== undefined) vitals.temperature_c = temperature;
  const context = {
    age_group: byId("age-group").value, symptoms,
    associated_symptoms: asList(byId("associated").value),
    medical_history: asList(byId("history").value),
    vulnerability_factors: asList(byId("vulnerability").value), vitals,
    confirmed_absent: [], unavailable_fields: [],
  };
  ["duration", "evolution", "intensity"].forEach((key) => { if (byId(key).value.trim()) context[key] = byId(key).value.trim(); });
  await assess(context, error, byId("submit"));
});

byId("follow-up-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = byId("follow-up-error");
  try {
    const context = applyGuidedAnswers();
    await assess(context, error, byId("follow-up-submit"));
  } catch (_) {
    error.textContent = copy[language].answerRequired;
    error.hidden = false;
  }
});

applyPreset("chest");
