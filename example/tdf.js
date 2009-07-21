var totalSeen=0;
var totalProcessed=0;
var recent = [];
var last_seen = 0;

function gotData(data, st) {
    try {
        last_seen = data.max;
        totalSeen += parseInt(data.saw);
    } catch(err) {
        // Weird data again.
    }

    $.each(data.res, function(idx, p) {
        try {
            if(recent.length > 10) {
                $('ul#lines li:last').remove();
                recent.shift();
            }
            $('<li>' + p[1] + '</li>').prependTo('#lines');
            recent.push(p[1]);
            totalProcessed++;
        } catch(err) {
            // Data didn't look like what we wanted.
            console.log("Bad data in loop.");
        }
    });

    // $('#seen').html(totalSeen);
    // $('#processed').html(totalProcessed);
}

function getData() {
    $.getJSON('/cmds/ping?n=' + last_seen, gotData);
}

