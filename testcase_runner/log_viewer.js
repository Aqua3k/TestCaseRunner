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

function buttonClicked(buttonNumber) {
    var checkboxs = getCheckboxList();
    if (buttonNumber === 1) {
        console.log(checkboxs);
    } else if (buttonNumber === 2) {
        // Do something else
    }
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
