window.onload = function() {
    updateTable();
};

function updateTable() {
    var data = JSON.stringify({ type: "0" });
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://localhost:5000/api/log_table", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                var responseText = xhr.responseText;
                document.getElementById('responseArea').innerHTML = responseText;
            } else {
                alert('HTTPリクエストが失敗しました。');
            }
        }
    };
    console.log(data);
    xhr.send(data);
}

function eraseLogFolder(checkboxList) {
    var data = JSON.stringify({
            type: "1",
            checkbox: checkboxList,
        });
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://localhost:5000/api/log_table", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.send(data);
}

function popupWindow() {
    var data = JSON.stringify({
        type: "2",
        checkbox: getCheckboxList(),
    });
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "http://localhost:5000/api/log_table", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
            
                // 新しいページを作成
                var newPage = window.open('', '_blank');

                // JSON文字列をJavaScriptオブジェクトに変換
                var data = JSON.parse(xhr.responseText);
                console.log(data);

                // テーブルの要素を生成してJSONデータを表として表示
                var table = newPage.document.createElement('table');
                var tableHead = newPage.document.createElement('thead');
                var tableBody = newPage.document.createElement('tbody');

                // ヘッダー行を作成
                var headerRow = newPage.document.createElement('tr');
                var keys = Object.keys(data);
                for (var i = 0; i < keys.length; i++) {
                    var headerCell = newPage.document.createElement('th');
                    headerCell.textContent = keys[i];
                    headerRow.appendChild(headerCell);
                }
                tableHead.appendChild(headerRow);

                // データ行を作成
                var rowKeys = Object.keys(data[keys[0]]);
                for (var j = 0; j < rowKeys.length; j++) {
                    var row = newPage.document.createElement('tr');
                    for (var k = 0; k < keys.length; k++) {
                    var cell = newPage.document.createElement('td');
                    cell.textContent = data[keys[k]][rowKeys[j]];
                    row.appendChild(cell);
                    }
                    tableBody.appendChild(row);
                }

                table.appendChild(tableHead);
                table.appendChild(tableBody);
                newPage.document.body.appendChild(table);
            } else {
                alert('HTTPリクエストが失敗しました。');
            }
        }
    };
    console.log(data);
    xhr.send(data);
}

function eraseButtonHandler() {
    console.log("delete button is clicked!");
    let checkboxList = getCheckboxList();
    if (checkboxList.length == 0) {
        alert('削除する対象を選択してください。');
        return;
    }
    eraseLogFolder(checkboxList);
    updateTable();
}

function diffButtonHandler() {
    console.log("diff button is clicked!");
    let checkboxList = getCheckboxList();
    if (checkboxList.length != 2) {
        alert('2つじゃないよ');
        return;
    }
    popupWindow();
}

function getCheckboxList() {
    let ret = [];
    var checkboxes = document.querySelectorAll('.groupedCheckbox');
    checkboxes.forEach(function(checkbox) {
        if (checkbox.checked) {
            ret.push(checkbox.id);
        }
    });
    return ret;
}
