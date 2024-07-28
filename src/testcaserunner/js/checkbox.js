const columnControls = document.getElementById("column-controls");
const table = document.getElementById("sortTable");
const headers = table.querySelectorAll("th");

// ヘッダーから列名を取得してチェックボックスを動的に生成
headers.forEach((header, index) => {
    const columnName = header.innerText;
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = `col-${index}`;
    checkbox.checked = true;  // 初期状態では全ての列を表示
    checkbox.onchange = () => toggleColumn(index);

    const label = document.createElement("label");
    label.htmlFor = checkbox.id;
    label.innerText = columnName;

    // チェックボックスとラベルをラッパーで囲む
    const container = document.createElement("div");
    container.className = "checkbox-container";
    container.appendChild(checkbox);
    container.appendChild(label);

    columnControls.appendChild(container);
});

function toggleColumn(index) {
    const cells = table.querySelectorAll(`th:nth-child(${index + 1}), td:nth-child(${index + 1})`);
    cells.forEach(cell => {
        cell.classList.toggle("hidden");
    });
}

