fetch('/api/apollo')
  .then(res => res.json())
  .then(data => populateTable(data))
  .catch(err => console.error("Error:", err));

function populateTable(data) {
  const head = document.getElementById("table-head");
  const body = document.getElementById("table-body");

  if (!data.length) return;

  const headers = Object.keys(data[0]);
  headers.forEach(key => {
    const th = document.createElement("th");
    th.textContent = key;
    head.appendChild(th);
  });

  data.forEach(row => {
    const tr = document.createElement("tr");
    headers.forEach(key => {
      const td = document.createElement("td");
      td.textContent = row[key];
      tr.appendChild(td);
    });
    body.appendChild(tr);
  });
}

