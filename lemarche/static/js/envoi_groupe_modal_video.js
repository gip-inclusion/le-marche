var tag = document.createElement('script');

tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

var player;
function onYouTubeIframeAPIReady() {
	player = new YT.Player('modal-player', {
		height: '100%',
		width: '100%',
		videoId: 'LXijOD6y92g',
		// events: {}
	});
}

function playVideo() {
	player.playVideo();
}

function stopVideo() {
	player.stopVideo();
}

$('#envoiGroupeModal').on('shown.bs.modal', function(e) {
	// start video automatically
	playVideo();
}).on('hide.bs.modal', function(e) {
	stopVideo();
});
