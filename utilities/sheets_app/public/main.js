const statusEl = document.getElementById("status");
const searchInput = document.getElementById("searchInput");
const refreshButton = document.getElementById("refreshButton");
const tableContainer = document.getElementById("tableContainer");

let cachedRows = [];
let headers = [];

const renderTable = (rows) => {
  if (!rows.length) {
    tableContainer.innerHTML = `<div class="empty">No rows found.</div>`;
    return;
  }

  headers = Array.from(
    rows.reduce((set, row) => {
      Object.keys(row).forEach((key) => set.add(key));
      return set;
    }, new Set())
  );

  const headerHtml = headers
    .map((header) => `<th>${header.replace(/_/g, " ")}</th>`)
    .join("");
  const rowsHtml = rows
    .map(
      (row) =>
        `<tr>${headers
          .map((header) => {
            const value = row[header] ?? "";
            if (header === "source_sheet") {
              return `<td><span class="pill">${value}</span></td>`;
            }
            if (header === "source_url") {
              return `<td><a href="${value}" target="_blank" rel="noopener" class="muted">link</a></td>`;
            }
            return `<td>${value}</td>`;
          })
          .join("")}</tr>`
    )
    .join("");

  tableContainer.innerHTML = `<table>
    <thead><tr>${headerHtml}</tr></thead>
    <tbody>${rowsHtml}</tbody>
  </table>`;
};

const filterRows = (query) => {
  if (!query) {
    renderTable(cachedRows);
    return;
  }
  const normalized = query.toLowerCase();
  const filtered = cachedRows.filter((row) =>
    headers.some((header) => String(row[header] ?? "").toLowerCase().includes(normalized))
  );
  renderTable(filtered);
};

const loadData = async (force = false) => {
  statusEl.textContent = force ? "Refreshing..." : "Loading data...";
  try {
    const response = await fetch(force ? "/refresh" : "/combined", {
      method: force ? "POST" : "GET",
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Request failed");
    }
    const payload = await response.json();
    cachedRows = force ? cachedRows : payload;
    if (force) {
      statusEl.textContent = `Refreshed: ${payload.rows} rows`;
      await loadData(false);
      return;
    }
    cachedRows = payload;
    renderTable(cachedRows);
    statusEl.textContent = `Loaded ${cachedRows.length} rows`;
  } catch (error) {
    console.error(error);
    statusEl.textContent = error.message;
    tableContainer.innerHTML = `<div class="empty">Error: ${error.message}</div>`;
  }
};

searchInput.addEventListener("input", (event) => filterRows(event.target.value));
refreshButton.addEventListener("click", () => loadData(true));

loadData();
