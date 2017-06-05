//global variables that act as conditional variables to define when a certain event is active such as when the sendTextMessage button has been hit
var gTextSent = [false];
//global variables that store the rows checked for swapping and their index
var gFirstChecked;
var gFirstCheckedRowIndex;
var gSecondChecked;
var gSecondCheckedRowIndex;
//global variable for the state of the timer
var globalTimer = [undefined];

//this script will be run on every refresh, or opening of the page, which will run the Update() function every 30 seconds
setInterval(Update, 30000);
setInterval(timer, 1000);

$("#loginModal").modal({ backdrop: "static" });

function securityCheck() {
    var pin = document.getElementById("psw").value;
    var url = "http://192.168.1.234:8080/verifyPin";
    var request = new XMLHttpRequest();

    request.onload = function () {
        var response = JSON.parse(request.responseText);
        if (response.result == "1") {
            $("#loginModal").modal("hide");
        } else if (response.result == "0") {
            document.getElementById("errorAlert").style.display = "block";
            setTimeout(function () { removeAlert("errorAlert") }, 3000);
            document.getElementById("securityPass").reset();
        }
    };

    request.onerror = function () {
        alert("There was an error, check your internet connection and submit the pin again");
    };

    request.open("POST", url, true);
    request.send("pin=" + pin);

    return false;
}

function removeAlert(id) {
    document.getElementById(id).style.display = "none";
}

function sendMessage(Element) {
    var url = "http://192.168.1.234:8080/sendTextMessage";
    var request = new XMLHttpRequest();
    var row = Element.parentNode.parentNode;
    var position = row.rowIndex;

    request.onload = function () {
        var response = JSON.parse(request.responseText);
        if (response.result == "-1") {
            alert("There was an error, or if a number was provided, the text could not be sent. Please try again");
        } else {
            var timer = row.getElementsByTagName("TD")[1];
            timer.innerHTML = "05:00";
            timer.style.color = "blue";
            globalTimer[position - 1] = setInterval(function(){fiveMinuteCountdown(timer,row);}, 1000);
            stationAvailableState(position,row);
            Update();
        }
    };

    request.onerror = function () {
        alert("The text could not be sent, check your internet connection and try again");
    };

    request.open("POST", url, true);
    request.send("position=" + position);
}

function stationAvailableState(position,row) {
    row.getElementsByTagName("BUTTON")[1].innerHTML = "No Show";
    row.getElementsByTagName("BUTTON")[0].innerHTML = "Arrived";
    row.getElementsByTagName("BUTTON")[0].onclick = function () { Delete(this) };
    document.getElementById("waitlistTable").rows[position].className = "yellow";
    if(row.getElementsByTagName("INPUT")[0].checked){
        row.getElementsByTagName("INPUT")[0].click();
    }
    row.getElementsByTagName("INPUT")[0].disabled = true;
    gTextSent[position - 1] = true;
    gTextSent.push(false);
    globalTimer.push(undefined);
}

function Update() {
    var url = "http://192.168.1.234:8080/refresh";
    var request = new XMLHttpRequest();

    request.onload = function () {
        
        var body = document.getElementById("waitlistTableBody");
        var numberOfRows = body.rows.length;
        
        for (var i = numberOfRows - 1; i > -1; i--){
            if (typeof gTextSent[i] != "undefined") {
                if (!gTextSent[i]) {
                    body.deleteRow(i);
                }
            } else {
                body.deleteRow(i);
            }
        }
        
        var response = JSON.parse(request.responseText);
        var table = response;
        var numberOfUsers = table.length;

        for (var i = 0; i < numberOfUsers; i++) {
            if (typeof gTextSent[i] != "undefined") {
                if (!gTextSent[i]) {
                    var row = body.insertRow(i);
                    row.className = "green";
                    row.innerHTML = "<td><input type='checkbox' class='selectBoxes' id='initial' onchange='checkmarkChangeForSwap(this)'> <custom>(" + (i + 1) + ")</custom></td><td id='timer'>" + table[i][2] + "</td><td class='userID'>" + table[i][0] + "</td><td>" + table[i][3] + "</td><td>" + table[i][1] + '</td><td id="centerData"><button type="button" id="greenButton" class="btn btn-success btn-lg" onclick="sendMessage(this)">Station Available</button> <button type="button" id="redButton" class="btn btn-danger btn-lg" onclick="Delete(this)">Cancel Turn</button></td>';
                }
            } else {
                var row = body.insertRow(i);
                row.innerHTML = "<td><input type='checkbox' class='selectBoxes' onchange='checkmarkChangeForSwap(this)'> <custom>(" + (i + 1) + ")</custom></td><td>" + table[i][2]  + "</td><td class='userID'>" + table[i][0] + "</td><td>" + table[i][3] + "</td><td>" + table[i][1] + '</td><td id="centerData"><button type="button" class="btn btn-danger btn-lg" onclick="Delete(this)">Cancel Turn</button></td>';
            }
        }

        document.getElementById("updateTime").innerHTML = 0;

        if (typeof gFirstChecked != "undefined") {
            var index = gFirstCheckedRowIndex;
            gFirstChecked = undefined;
            document.getElementsByClassName("selectBoxes")[index - 1].click();
        }

        if (typeof gSecondChecked != "undefined") {
            var index = gSecondCheckedRowIndex;
            gSecondChecked = undefined;
            document.getElementsByClassName("selectBoxes")[index - 1].click();
        }
    };

    request.onerror = function () {
        alert("Update failed, check your internet connection and try again");
    };

    request.open("POST", url, true);
    request.send();
}

function Delete(Element) {
    var uniqueID = Element.parentNode.parentNode.getElementsByClassName("userID")[0].innerHTML;
    var buttonText = Element.innerHTML;
    var state = changeStatistics(buttonText);
    var url = "http://192.168.1.234:8080/delete";
    var request = new XMLHttpRequest();
    var response;

    request.onload = function () {
        response = JSON.parse(request.responseText);
        if (response.result == "1") {
            var totalRows = Element.parentElement.parentElement.parentElement.rows.length;
            var targetRow = Element.parentElement.parentElement;
            var rowNumber = targetRow.rowIndex;

            if (typeof gTextSent[rowNumber - 1] != "undefined" && gTextSent[rowNumber - 1]) {
                if (typeof globalTimer[rowNumber - 1] != "undefined") {
                    clearInterval(globalTimer[rowNumber - 1]);
                }
                
                if(rowNumber == 1 && totalRows == 1){
                    globalTimer[0] = undefined;
                    gTextSent[0] = false;
                    if(gTextSent.length != 1){
                        globalTimer.splice(1, 1);
                        gTextSent.splice(1, 1);    
                    }    
                } else {
                    globalTimer.splice(rowNumber - 1, 1);
                    gTextSent.splice(rowNumber - 1, 1);
                    shiftPosition(rowNumber);
                }
            }

            if (typeof gFirstChecked != "undefined") {
                gFirstChecked.click();
            }

            if (typeof gSecondChecked != "undefined") {
                gSecondChecked.click();
            }

            document.getElementById("waitlistTable").deleteRow(rowNumber);
            Update();
        }
    };

    request.onerror = function () {
        alert("Removal failed, check your internet connection and try again");
    };

    request.open("POST", url, true);
    request.send("uniqueID=" + uniqueID + "&state=" + state);
}

function changeStatistics(buttonText) {
    if (buttonText == "Arrived") {
        return 0;
    } else if (buttonText == "No Show") {
        return 1;
    } else if (buttonText == "Cancel Turn") {
        return 2;
    }
}

function shiftPosition(position){
    var body = document.getElementById("waitlistTableBody").rows;
    var numberOfRows = body.length;
    
    for(var i = position; i < numberOfRows; i++){
        body[i].getElementsByTagName("custom")[0].innerHTML = "(" + (i) + ")";
    }
}

function timer() {
    (document.getElementById("updateTime").innerHTML)++;
}

function fiveMinuteCountdown(timer,row) {
    var time = timer.innerHTML;
    var position = row.rowIndex;
    var minutes = parseInt(time.substring(0, 2));
    var seconds = parseInt(time.substring(3, 5));

    seconds--;

    if (minutes == 0 && seconds == 0) {
        clearInterval(globalTimer[position - 1]);
        globalTimer[position - 1] = undefined;
        setTimeout(function(){displayNoShow(timer,row);}, 5000);
    }

    if (seconds == -1) {
        minutes--;
        seconds = 59;
    }

    if (seconds < 10) {
        seconds = "0" + seconds;
    }

    timer.innerHTML = "0" + minutes + ":" + seconds;

    if (minutes == 2 && seconds == 30) {
        timer.style.color = "red";
    }

}

function displayNoShow(timer,row) {
    document.getElementById("waitlistTable").rows[row.rowIndex].className = "red";
    timer.style.color = "blue";
}

function checkmarkChangeForSwap(checkmarkElement) {
    if (checkmarkElement.checked) {
        //checkmark was checked, store in either first or second checked variable, if both full, give an alert
        if (typeof gFirstChecked == "undefined") {
            gFirstChecked = checkmarkElement;
            gFirstCheckedRowIndex = checkmarkElement.parentNode.parentNode.rowIndex;
        } else if (typeof gSecondChecked == "undefined") {
            gSecondChecked = checkmarkElement;
            gSecondCheckedRowIndex = checkmarkElement.parentNode.parentNode.rowIndex;
        } else {
            alert("Two customers have already been selected for swap, deselect one of them to select this one");
            checkmarkElement.checked = false;
        }
    } else {
        if (gFirstChecked == checkmarkElement) {
            gFirstChecked = undefined;
        } else if (gSecondChecked == checkmarkElement) {
            gSecondChecked = undefined;
        }
    }
}

function swapCustomers() {
    if (typeof gFirstChecked != "undefined" && typeof gSecondChecked != "undefined") {
        var idOne = gFirstChecked.parentNode.parentNode.getElementsByClassName("userID")[0].innerHTML;
        var idTwo = gSecondChecked.parentNode.parentNode.getElementsByClassName("userID")[0].innerHTML;
        var url = "http://192.168.1.234:8080/swap";
        var request = new XMLHttpRequest();

        request.onload = function () {
            var response = JSON.parse(request.responseText);
            if (response.result == "1") {
                gFirstChecked.parentNode.parentNode.getElementsByClassName("selectBoxes")[0].click();
                gSecondChecked.parentNode.parentNode.getElementsByClassName("selectBoxes")[0].click();
                Update();
                alert("Success!\n\n" + idOne + " and " + idTwo + " have been switched!");
            }
        };

        request.onerror = function () {
            alert("There was an error, check your internet connection and try to swap again");
        };

        request.open("POST", url, true);
        request.send("idOne=" + idOne + "&idTwo=" + idTwo);
    } else {
        alert("Two rows must be selected for a swap to be possible");
    }
}

function flushWaitlist() {
    $("#flushModal").modal({ backdrop: "static" });
}

function securityCheckForFlush() {
    var pin = document.getElementById("pswTwo").value;
    var url = "http://192.168.1.234:8080/verifyPin";
    var request = new XMLHttpRequest();

    request.onload = function () {
        var response = JSON.parse(request.responseText);
        if (response.result == "1") {
            $("#flushModal").modal("hide");
            document.getElementById("securityPassTwo").reset();
            removeEveryone();
        } else if (response.result == "0") {
            document.getElementById("errorAlertTwo").style.display = "block";
            setTimeout(function () { removeAlert("errorAlertTwo") }, 3000);
            document.getElementById("securityPassTwo").reset();
        }
    };

    request.onerror = function () {
        alert("There was an error, check your internet connection and submit the pin again");
    };

    request.open("POST", url, true);
    request.send("pin=" + pin);

    return false;
}

function removeEveryone(){
    var url = "http://192.168.1.234:8080/emptyWaitlist";
    var request = new XMLHttpRequest();

    request.onload = function () {
        var response = JSON.parse(request.responseText);
        if (response.result == "1") {
            Update();
        }
    };

    request.onerror = function () {
        alert("Error: the waitlist could not be emptied, try again");
    };

    request.open("POST", url, true);
    request.send();
}

function hideFlushModal() {
    $('#flushModal').modal("hide");
}

