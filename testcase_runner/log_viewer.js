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
                const newWindow = window.open();
                var responseText = xhr.responseText;
                newWindow.document.write(responseText);
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