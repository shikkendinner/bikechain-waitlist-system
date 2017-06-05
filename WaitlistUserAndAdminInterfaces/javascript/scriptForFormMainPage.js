totalWaiting();
setInterval(totalWaiting, 30000);

function totalWaiting() {
    var url = "http://192.168.1.234:8080/countTotal";
    var request = new XMLHttpRequest();

    request.onload = function () {
        var response = JSON.parse(request.responseText);
        var tablelength = response.count;
        var minutes = response.avgMinutes;
        var hours = response.avgHours;

        var time = hours + (hours == "1" ? " hour ":" hours ") + " and " + minutes + (minutes == "1" ? " minute":" minutes");
        document.getElementById("people").innerHTML = tablelength;
        /*document.getElementById("time").innerHTML = time;*/
    };

    request.onerror = function () {
        alert("Error! Refresh the page");
    };

    request.open("POST", url, true);
    request.send();
}