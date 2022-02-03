var tag = document.createElement('script');

tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

var player;
function onYouTubeIframeAPIReady() {
	player = new YT.Player('modal-player', {
		height: '100%',
		width: '100%',
		videoId: 'Iju6-B2pLcg',
		events: {
			'onReady': onPlayerReady,
			'onStateChange': onPlayerStateChange
		}
	});
}

function onPlayerReady(event) {
	event.target.playVideo();
}

var done = false;
function onPlayerStateChange(event) {
	if (event.data == YT.PlayerState.PLAYING && !done) {
		setTimeout(stopVideo, 6000);
		done = true;
	}
}

function playVideo() {
	player.playVideo();
}

function stopVideo() {
	player.stopVideo();
}

$('#envoiGroupeModal').on('shown.bs.modal', function(e) {
	playVideo();
}).on('hide.bs.modal', function(e) {
	stopVideo();
})
