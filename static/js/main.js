$(".list-group-item").click(function() {
    if (this.classList.contains("active")) {
        this.classList.remove("active");
    } else {
        this.classList.add("active");
    }
});

function getSelectedPlaylists() {
    let playlists = document.getElementsByClassName("list-group-item list-group-item-action d-flex justify-content-between align-items-center playlists active");

    if (playlists.length >= 1) {
        let result = [];
        for (let i = 0; i < playlists.length; i++) {
            result.push(playlists[i].getAttribute("data-id"));
        }

        return result;
    } else {
        return false;
    }
}

function getPlaylists() {
    let val_tag = document.getElementById('selected_playlists');
    val_tag.value = getSelectedPlaylists();
}

function validateSelectPlaylists() {
    let playlists = document.getElementsByClassName("list-group-item list-group-item-action d-flex justify-content-between align-items-center playlists active");
    if (playlists.length >= 1) {
        return true;
    } else {
        alert("Please select at least one (1) playlist");
        return false;
    }
}