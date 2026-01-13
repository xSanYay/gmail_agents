async function fetchJson(url) {
  const res = await fetch(url, { headers: { "Accept": "application/json" } });
  const text = await res.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    json = { raw: text };
  }
  if (!res.ok) {
    const msg = json?.detail || json?.raw || `Request failed: ${res.status}`;
    throw new Error(msg);
  }
  return json;
}

function qs(selector) {
  return document.querySelector(selector);
}

const connectBtn = qs("#connect");
if (connectBtn) {
  connectBtn.addEventListener("click", () => {
    window.location.href = "/auth/start";
  });
}

const filtersForm = qs("#filters");
if (filtersForm) {
  filtersForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const status = qs("#status");
    const results = qs("#results");
    status.textContent = "Loading...";
    results.innerHTML = "";

    const form = new FormData(filtersForm);
    const params = new URLSearchParams();

    for (const [k, v] of form.entries()) {
      const val = String(v || "").trim();
      if (val) params.set(k, val);
    }

    try {
      const data = await fetchJson(`/gmail/messages?${params.toString()}`);
      status.textContent = `Query: ${data.query}`;

      for (const msg of data.messages || []) {
        const li = document.createElement("li");
        li.className = "result";
        li.innerHTML = `
          <div class="subject">${(msg.subject || "(no subject)").replaceAll("<", "&lt;")}</div>
          <div class="meta">From: ${(msg.from_email || "?").replaceAll("<", "&lt;")} • ${(msg.date || "").replaceAll("<", "&lt;")}</div>
          <div class="snippet">${(msg.snippet || "").replaceAll("<", "&lt;")}</div>
        `;
        results.appendChild(li);
      }

      if (!data.messages || data.messages.length === 0) {
        const li = document.createElement("li");
        li.className = "muted";
        li.textContent = "No messages found.";
        results.appendChild(li);
      }
    } catch (err) {
      status.textContent = `Error: ${err.message}`;
    }
  });
}
