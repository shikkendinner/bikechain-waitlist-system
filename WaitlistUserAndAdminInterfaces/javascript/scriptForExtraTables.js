function UpdateLogs() {
    var url = "http://192.168.1.234:8080/getLogs";
    var request = new XMLHttpRequest();

    request.onload = function () {
        var response = JSON.parse(request.responseText);
        $('#logTable').DataTable({
            data: response,
            "order": [[1, 'asc']]
        });
    };

    request.onerror = function () {
        alert("Error: refresh the page");
    };

    request.open("POST", url, true);
    request.send();
}

function UpdateNoShow() {
    var url = "http://192.168.1.234:8080/getNoShow";
    var request = new XMLHttpRequest();

    request.onload = function () {
        var response = JSON.parse(request.responseText);
        $('#noShowTable').DataTable({
            data: response
        });
    };

    request.onerror = function () {
        alert("Error: refresh the page");
    };

    request.open("POST", url, true);
    request.send();
}