function generateTable(e) {
  // form のデフォルト動作（送信・リロード）を止める。
  e.preventDefault();

  const num = Number(document.getElementById("mt-input").value);
  const table = document.getElementById("mt-table");

  table.innerHTML = `
    <tr>
      <th>敵の行軍時間</th>
      <th>兵を送るタイミング<br>(集結残り時間)</th>
    </tr>
  `;

  for (let i = 15; i <= 50; i++) {
    const row = document.createElement("tr");

    const cell1 = document.createElement("td");
    cell1.textContent = i;

    const cell2 = document.createElement("td");
    cell2.textContent = i - num;

    row.appendChild(cell1);
    row.appendChild(cell2);
    table.appendChild(row);
  }
}

document.getElementById("generate-btn").addEventListener("click", generateTable);
