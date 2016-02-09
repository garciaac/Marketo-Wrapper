/**
 * @author      Andrew Garcia <angarcia@marketo.com>
 *
 *  This module contains the services necesary for manipulating the Marketo API
 */
var REST = REST || {},
    http = require('https');

/*********************************************************************
 *                                                                   *
 *                          Initialization                           *
 *                                                                   *     
 *********************************************************************/

REST.munchkinId = "679-WJZ-355";
REST.clientId = "a4e379b7-b139-49c6-a2e6-aa485f15ef16";
REST.clientSecret = "A7nXl10KIuz5TXTTtddZoTskszNwMfPR";
REST.accessToken = "4659ff5e-1775-45da-a9e2-1480dd7ab729:ab";
REST.options = {
    host: REST.munchkinId + ".mktorest.com",
    port: 443
};
REST.expireTime = 0;

/*********************************************************************
 *                                                                   *
 *                          Authentication                           *
 *                                                                   *     
 *********************************************************************/

REST.generateAccessToken = function() {
    // First, we need to build the request URL.
    var tokenRequest = "/identity/oauth/token?grant_type=client_credentials&" +
        "client_id=" + this.clientId + "&client_secret=" + this.clientSecret,
        method = "GET",
        data = "";

    this.options.path = tokenRequest;
    this.options.method = method;

    this.genericRequest(tokenRequest, method, null, null, null, function(response) {
        this.expireTime = (new Date).getTime() + response["expires_in"];
        this.accessToken = response["access_token"];
        console.log(this.accessToken);
    });
};

/*********************************************************************
 *                                                                   *
 *                       Generic Functions                           *
 *                                                                   *     
 *********************************************************************/

REST.genericAPICall = function(call, method, contentType, payload, headers, fn) {

    headers = headers || {};
    
//    if (this.expireTime < (new Date).getTime()) {
//        this.generateAccessToken()
//    }

    this.options.path = call;
    this.options.method = method;

    headers["Authorization"] = "Bearer " + this.accessToken;
    headers["Content-type"] = contentType;

    this.options.headers = headers;
    this.genericRequest(call, method, contentType, payload, headers, function (response) {
        fn(response);
    });
};

REST.genericRequest = function(call, method, contentType, payload, headers, fn) {
    
    contentType = contentType || "application/json";
    payload = payload || {};

//    console.log("CALL: " + call);
//    console.log("METHOD: " + method);
//    console.log("CONTENT-TYPE: " + contentType);
//    console.log("PAYLOAD: " + JSON.stringify(payload));
//    console.log("HEADERS: " + JSON.stringify(headers));
//    console.log("OPTIONS " + JSON.stringify(this.options));

    var request = http.request(this.options, function(response) {
            console.log('STATUS: ' + response.statusCode);
//            console.log('HEADERS: ' + JSON.stringify(response.headers));
            response.setEncoding('utf8');
            response.on('data', function(chunk) {
                console.log('BODY: ' + chunk);
                fn(chunk);
            });
        });

    request.on('error', function(e) {
        console.log('problem with request: ' + e.message);
    });

    request.write(JSON.stringify(payload));
    request.end();
}

/*********************************************************************
 *                                                                   *
 *                            API Calls                              *
 *                                                                   *     
 *********************************************************************/

REST.createUpdateLeads = function(leads, action, lookupField, isAsync, partition) {
    
    var call = "/rest/v1/leads.json?",
        method = "POST",
        payload = {"input": leads};
    
    if (action != null) {
        payload["action"] = action;
    }
    if (lookupField != null) {
        payload["lookupField"] = lookupField;
    }
    if (isAsync != null) {
        payload["asyncProcessing"] = isAsync;
    }
    if (partition != null) {
        payload["partitionName"] = partition;
    }
    
    this.genericAPICall(call, method, null, payload, null, function(response) {
       console.log(response); 
    });
}

REST.addLeadActivities = function(activities) {
    
    var call = "/rest/v1/activities/external.json?",
        method = "POST",
        payload = {"input": activities};
    
    this.genericAPICall(call, method, "application/json", payload, null, function(response) {
       console.log(response); 
    });
}

var main = function() {
    var fs = require("fs"),
        inviteData = [];
    fs.readFileSync("Trello/invite-activities.json").toString().split("\n").forEach(function (line) {
//        console.log(line);
        inviteData.push(JSON.parse(line));
    });
    var i,j,
        chunk = 300;
    
    for (i=0,j=inviteData.length; i<j; i+=chunk) {
        REST.addLeadActivities(inviteData.slice(i,i+chunk));
    }
    
}();