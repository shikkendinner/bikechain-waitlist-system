if (typeof (Storage) !== "undefined") {
    var userID = localStorage.uniqueID;
    document.getElementById("idInStorage").innerHTML = userID;
    var url = "http://192.168.1.234:8080/queryList";

    var request = new XMLHttpRequest();

    request.onload = function () {
        var response = JSON.parse(request.responseText);
        var numberAhead = response.result - 1;
        var stationAvailable = response.stationAvailable != "N/A" ? true : false;
        if (numberAhead == "0") {
            var phone = response.phone;

            if (!stationAvailable) {
                document.getElementById("numberAhead").innerHTML = "It is your turn soon!";
                if (phone != "0") {
                    document.getElementById("support").innerHTML = "you will receive a text message on the number you provided once it is your turn";
                } else {
                    document.getElementById("support").innerHTML = "check the webapp more frequently until it is your turn, or wait at the workshop";
                }
            } else {
                document.getElementById("numberAhead").innerHTML = "It is now your turn!";
                document.getElementById("support").innerHTML = "please arrive at the workshop within 5 minutes or your turn will be cancelled";
            }

        } else if (response.result != "-1") {
            document.getElementById("numberAhead").innerHTML = numberAhead;
            document.getElementById("support").innerHTML = "user" + (numberAhead == "1" ? "" : "s") + " ahead of you on the list";
        } else {
            document.getElementById("numberAhead").innerHTML = "Oops";
            document.getElementById("support").innerHTML = "your name is not on the list";
        }
    };

    request.onerror = function () {
        document.getElementById("numberAhead").innerHTML = "There was an error";
        document.getElementById("support").innerHTML = "try again or check your internet connection";
    };

    request.open("POST", url, true);
    request.send("uniqueID=" + userID);

} else {
    document.getElementById("numberAhead").innerHTML = "Error";
    document.getElementById("support").innerHTML = "This browser is not compatible, please use another browser";
}

function returnToMainPage() {
    if (typeof (Storage) !== "undefined") {
        localStorage.removeItem("uniqueID");
        location.assign("../html/main.html");
    }
}
