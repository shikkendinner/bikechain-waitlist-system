// the code below runs as soon as the page starts to load
if (typeof (Storage) !== "undefined") {
    if (localStorage.uniqueID) {
        location.assign("../html/result.html");
    }
}

// runs once the "search in waitlist" button is clicked
function validateAndProceed() {
    var uniqueID = document.getElementById("uniqueID").value.replace(/\s/g, "");
    if (uniqueID == "") {
        document.getElementById("errorAlert").style.display = "block";
        setTimeout(function () { removeAlert("errorAlert") }, 3000);
        return false;
    } else {
        if (typeof (Storage) !== "undefined") {
            localStorage.setItem("uniqueID", uniqueID);
        } 
        return true;
    }
}

// removes the alert from the screen
function removeAlert(id) {
    document.getElementById(id).style.display = "none";
}