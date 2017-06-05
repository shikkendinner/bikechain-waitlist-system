//code that implements the input type "date" (from Google) in Firefox and puts it in the yy-mm-dd pattern
webshims.setOptions('forms-ext', { types: 'date' });
webshims.polyfill('forms forms-ext');
$.webshims.formcfg = {
    en: {
        dFormat: '-',
        dateSigns: '-',
        patterns: {
            d: "yy-mm-dd"
        }
    }
};

//reset the form
document.getElementById("statForm").reset();

function getStats() {
    var dateFrom = document.getElementById("from").value;
    var dateTo = document.getElementById("to").value;

    var url = "http://192.168.1.234:8080/getStats";
    var request = new XMLHttpRequest();

    request.onload = function () {
        var response = JSON.parse(request.responseText);

        if (dateFrom != dateTo) {
            document.getElementById("textBeforeStats").innerHTML = 'Statistics for dates between <strong id="dateFrom"></strong> and <strong id="dateTo"></strong> :'
            document.getElementById("dateFrom").innerHTML = dateFrom;
            document.getElementById("dateTo").innerHTML = dateTo;
        } else {
            document.getElementById("textBeforeStats").innerHTML = 'Statistics for the date <strong id="dateFrom"></strong> :'
            document.getElementById("dateFrom").innerHTML = dateFrom;
        }

        document.getElementById("totalUsers").innerHTML = response.added;
        document.getElementById("gavePhoneNum").innerHTML = response.msgSent;
        document.getElementById("totalArrived").innerHTML = response.arrived;
        document.getElementById("logBook").innerHTML = response.logBook;
        document.getElementById("totalNoShow").innerHTML = response.noShow;
        document.getElementById("totalCancelled").innerHTML = response.cancelled;
        document.getElementById("totalFlushed").innerHTML = response.flushedFromWaitlist;
        
        var minutes = response.avgMinutes;
        var hours = response.avgHours;

        var time = hours + (hours == "1" ? " hour ":" hours ") + " and " + minutes + (minutes == "1" ? " minute":" minutes");
        
        document.getElementById("waitingTime").innerHTML = time;
        document.getElementById("stats").style.display = "block";
        document.getElementById("statForm").reset();
    };

    request.onerror = function () {
        alert("Error: refresh the page and try again");
    };

    request.open("POST", url, true);
    request.send("dateFrom=" + dateFrom + "&dateTo=" + dateTo);

    return false;
}