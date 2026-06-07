const TYPE_LABELS = {
  social_post: "Пост для соцсетей",
  article: "Экспертная статья",
  newsletter: "Email-рассылка",
};

let pricing = {};

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

function toast(msg) {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2600);
}

function fmtRub(n) {
  return new Intl.NumberFormat("ru-RU").format(n) + " ₽";
}

async function loadHealth() {
  const h = await api("/api/health");
  const badge = document.getElementById("llm-badge");
  if (h.llm_mode === "gigachat") {
    badge.textContent = "GigaChat: подключён";
    badge.className = "llm-badge real";
  } else {
    badge.textContent = "Демо-режим (без ключа LLM)";
    badge.className = "llm-badge stub";
  }
}

async function loadPricing() {
  pricing = await api("/api/pricing");
  const sel = document.getElementById("order-type");
  sel.innerHTML = "";
  for (const [type, price] of Object.entries(pricing)) {
    const opt = document.createElement("option");
    opt.value = type;
    opt.textContent = `${TYPE_LABELS[type] || type} — ${fmtRub(price)}`;
    sel.appendChild(opt);
  }
}

async function loadClients() {
  const clients = await api("/api/clients");
  const sel = document.getElementById("order-client");
  const current = sel.value;
  sel.innerHTML = '<option value="">Выберите клиента…</option>';
  for (const c of clients) {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.name + (c.industry ? ` · ${c.industry}` : "");
    sel.appendChild(opt);
  }
  sel.value = current;
  return clients;
}

async function loadRevenue() {
  const r = await api("/api/revenue");
  document.getElementById("stat-revenue").textContent = fmtRub(r.revenue_rub);
  document.getElementById("stat-pipeline").textContent = fmtRub(r.pipeline_rub);
  document.getElementById("stat-done").textContent = r.orders_done;
  document.getElementById("stat-total").textContent = r.orders_total;
}

async function loadOrders() {
  const [orders, clients] = await Promise.all([api("/api/orders"), api("/api/clients")]);
  const byId = Object.fromEntries(clients.map((c) => [c.id, c]));
  const wrap = document.getElementById("orders");
  if (!orders.length) {
    wrap.innerHTML = '<p class="empty">Заказов пока нет. Добавьте клиента и создайте бриф.</p>';
    return;
  }
  wrap.innerHTML = "";
  for (const o of orders) {
    const client = byId[o.client_id];
    const div = document.createElement("div");
    div.className = "order";
    div.innerHTML = `
      <div class="order-head">
        <span class="order-title">${escapeHtml(o.topic)}</span>
        <span class="price">${fmtRub(o.price_rub)}</span>
      </div>
      <div class="order-meta">
        ${client ? escapeHtml(client.name) : "—"} ·
        ${TYPE_LABELS[o.content_type] || o.content_type}
        <span class="badge ${o.status}">${statusLabel(o.status)}</span>
      </div>
      <div class="order-actions"></div>`;
    const actions = div.querySelector(".order-actions");
    if (o.status === "done") {
      const view = mkBtn("Посмотреть контент", "ghost", () => viewDeliverable(o.id));
      actions.appendChild(view);
    } else {
      const run = mkBtn("▶ Запустить агентов", "", async (btn) => {
        btn.disabled = true;
        btn.textContent = "Агенты работают…";
        try {
          await api(`/api/orders/${o.id}/run`, { method: "POST" });
          toast("Контент готов!");
          await refresh();
          await viewDeliverable(o.id);
        } catch (e) {
          toast("Ошибка: " + e.message);
          await refresh();
        }
      });
      actions.appendChild(run);
    }
    wrap.appendChild(div);
  }
}

function mkBtn(label, cls, onClick) {
  const b = document.createElement("button");
  b.textContent = label;
  if (cls) b.className = cls;
  b.addEventListener("click", () => onClick(b));
  return b;
}

function statusLabel(s) {
  return { new: "новый", in_progress: "в работе", done: "готово", failed: "ошибка" }[s] || s;
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

async function viewDeliverable(orderId) {
  const d = await api(`/api/orders/${orderId}/deliverable`);
  const panel = document.getElementById("result-panel");
  const result = document.getElementById("result");
  result.innerHTML = `
    <div class="result-block">
      <h3>🧭 Стратегия (Стратег)</h3><pre>${escapeHtml(d.strategy)}</pre>
    </div>
    <div class="result-block">
      <h3>✦ Финальный контент (после Редактора)</h3><pre>${escapeHtml(d.final)}</pre>
    </div>
    <div class="result-block">
      <h3>📝 Черновик (Копирайтер)</h3><pre>${escapeHtml(d.draft)}</pre>
    </div>
    <p class="empty">Модель: ${escapeHtml(d.llm_model)} · токенов: ${d.tokens_used}</p>`;
  panel.hidden = false;
  panel.scrollIntoView({ behavior: "smooth" });
}

async function refresh() {
  await Promise.all([loadOrders(), loadRevenue(), loadClients()]);
}

document.getElementById("client-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    await api("/api/clients", {
      method: "POST",
      body: JSON.stringify({
        name: f.get("name"),
        industry: f.get("industry"),
        brand_voice: f.get("brand_voice"),
      }),
    });
    e.target.reset();
    toast("Клиент добавлен");
    await loadClients();
  } catch (err) {
    toast("Ошибка: " + err.message);
  }
});

document.getElementById("order-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  if (!f.get("client_id")) return toast("Сначала выберите клиента");
  try {
    await api("/api/orders", {
      method: "POST",
      body: JSON.stringify({
        client_id: Number(f.get("client_id")),
        content_type: f.get("content_type"),
        topic: f.get("topic"),
        brief: f.get("brief"),
      }),
    });
    e.target.reset();
    toast("Заказ создан");
    await refresh();
  } catch (err) {
    toast("Ошибка: " + err.message);
  }
});

document.getElementById("result-close").addEventListener("click", () => {
  document.getElementById("result-panel").hidden = true;
});

(async function init() {
  await Promise.all([loadHealth(), loadPricing()]);
  await refresh();
})();
