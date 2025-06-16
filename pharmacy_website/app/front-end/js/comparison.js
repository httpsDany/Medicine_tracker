document.addEventListener("DOMContentLoaded", () => {
  const filterSelect = document.getElementById("filter");

  // Initial load
  loadData(filterSelect.value);

  // On filter change
  filterSelect.addEventListener("change", () => {
    loadData(filterSelect.value);
  });
});

function buildTable(data) {
  const thead = document.getElementById("table-head");
  const tbody = document.getElementById("table-body");

  thead.innerHTML = `
    <th>Name</th>
    <th>Brand</th>
    <th>Source</th>
    <th>Price</th>
    <th>Discount</th>
    <th>Best Price</th>
    <th>Best Offer</th>
    <th>Action</th>
  `;

  data.forEach(item => {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${item.name}</td>
      <td>${item.brand}</td>
      <td>${item.source || ""}</td>
      <td>${item.price || ""}</td>
      <td>${item.discount || ""}</td>
      <td>
    <input type="number" 
           value="${item.best_price !== null ? item.best_price : ''}" 
           id="input-${item.name.replace(/\s+/g, "_")}-${item.brand.replace(/\s+/g, "_")}" />
  </td>
      <td>${item.best_offer !== null ? item.best_offer : ""}</td>
      <td>
    <button class="save-btn">Save</button>
    <button class="reset-btn">Reset</button>
  </td>
    `;
	// Save button
row.querySelector(".save-btn").addEventListener("click", async () => {
  const input = document.getElementById(`input-${item.name.replace(/\s+/g, "_")}-${item.brand.replace(/\s+/g, "_")}`);
  const bestPrice = input ? parseFloat(input.value) : null;

  await fetch("/api/create_and_update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: item.name,
      brand: item.brand,
      best_price: bestPrice
    })
  });

  loadData(document.getElementById("filter").value);
});

// Reset button
row.querySelector(".reset-btn").addEventListener("click", async () => {
  await fetch("/api/reset-entry", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: item.name, brand: item.brand })
  });

  loadData(document.getElementById("filter").value);
});

    tbody.appendChild(row);
  });
}

function loadData(filter) {
  fetch(`/api/create_and_update?filter_by=${filter}`, {
    method: 'POST'
  })
    .then(res => res.json())
    .then(data => {
      console.log("Fetched data:", data);
      clearTable();
      buildTable(data);
    })
    .catch(err => console.error("Error:", err));
}

function clearTable() {
  document.getElementById("table-head").innerHTML = "";
  document.getElementById("table-body").innerHTML = "";
}
document.getElementById("save-all-btn").addEventListener("click", async () => {
  const rows = document.querySelectorAll("#table-body tr");
  const payload = [];

  rows.forEach(row => {
    const cells = row.querySelectorAll("td");
    const name = cells[0]?.textContent.trim();
    const brand = cells[1]?.textContent.trim();
    const input = row.querySelector("input[type='number']");
    const bestPrice = input && input.value !== "" ? parseFloat(input.value) : null;

    if (name && brand) {
      payload.push({
        name: name,
        brand: brand,
        best_price: bestPrice
      });
    }
  });

  if (payload.length > 0) {
    await fetch("/api/create_and_update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    loadData(document.getElementById("filter").value);
  }
});

