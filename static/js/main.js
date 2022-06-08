$(".selectable").click(function() {
    if (this.classList.contains("active")) {
        this.classList.remove("active");
    } else {
        this.classList.add("active");
    }
});

function getSelectedPlaylists() {
    let playlists = document.getElementsByClassName("list-group-item selectable list-group-item-action d-flex justify-content-between align-items-center playlists active");

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
    let playlists = document.getElementsByClassName("list-group-item selectable list-group-item-action d-flex justify-content-between align-items-center playlists active");
    if (playlists.length >= 1) {
        return true;
    } else {
        alert("Please select at least one (1) playlist");
        return false;
    }
}

function getSelectedArtists() {
    let artists = document.getElementsByClassName("list-group-item selectable list-group-item-action d-flex justify-content-between align-items-center artists active");

    if (artists.length >= 1) {
        let result = [];
        for (let i = 0; i < artists.length; i++) {
            result.push(artists[i].getAttribute("data-id"));
        }

        return result;
    } else {
        return false;
    }
}

function getArtists() {
    let val_tag = document.getElementById('selected_artists');
    val_tag.value = getSelectedArtists();
}

function validateSelectArtists() {
    let artists = document.getElementsByClassName("list-group-item selectable list-group-item-action d-flex justify-content-between align-items-center artists active");
    if (artists.length >= 1) {
        return true;
    } else {
        alert("Please select at least one (1) artist");
        return false;
    }
}