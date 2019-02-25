function refreshPage()
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
            result = JSON.parse(xmlHttp.response);
            if (result["refresh"] == true) {
                window.location.reload(1);
            }
        }
    }
    xmlHttp.open("GET", "http://localhost:8001/_refresh", true);
    xmlHttp.send(null);
}

setInterval(refreshPage, 2000);