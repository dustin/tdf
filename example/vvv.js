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
            if(recent.length > 11) {
                $('ul#lines li:last').remove();
                recent.shift();
            }
            var classname = p[1].op + " " + p[1].result.toLowerCase().replace(" ", "-");
            var line = p[1].op + " " + p[1].key + " " + p[1].result;
            $('<li class="' + classname  + '">' + line + '</li>').prependTo('#lines');
            recent.push(p[1]);
            totalProcessed++;
        } catch(err) {
            // Data didn't look like what we wanted.
            console.log("Bad data in loop.");
        }
    });
}

function getData() {
    $.getJSON('/cmds/dtrace?n=' + last_seen, gotData);
}

