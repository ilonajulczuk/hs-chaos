$(function() {
    if ("WebSocket" in window) {
        ws = new WebSocket("ws://127.0.0.1:8000/websocket");
        ws.onmessage = function (msg) {
            var message = JSON.parse(msg.data);
            $("p#log").append(message.output + '<hr />');
        };
    };


    $(".table_form").on('submit', function(e){
        var id = $('#table_id').val();
        var username = $('#username').val()
        if (username == ''){
            alert('Provide username before claiming!');
            e.preventDefault();
        }
        ws.send(JSON.stringify({'table_id': id, 'username': username}));
    });

    window.onbeforeunload = function() {
        ws.onclose = function () {};
        ws.close()
    };
});

