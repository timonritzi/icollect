$("#submit").click(function () {

    $("#submit").prop('disabled', true)
    $(".input").removeClass().addClass("input-hidden")

    let url = $("#url").val();

    let api = "https://icollect.timonritzi.com:1337";

    if (url) {

        $(".hidden").removeClass().addClass("show")
        fetch(api, {

            method: 'post',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'url': url
            })

        }).then((response) => {

            return response.json();


        }).then((data) => {

            let sessionId = data["sessionid"]
            let directory = sessionId + ".zip"
            $("#submit").prop('disabled', false)
            $("#url").val("")
            $(".show").removeClass().addClass("hidden")
            $("#link").attr("href", `https://icollect.timonritzi.com/media/${directory}`)
            $(".hidden2").removeClass().addClass("show2")


        });

    }

});

$("#refresh").click(function (){
    location.reload()
})





