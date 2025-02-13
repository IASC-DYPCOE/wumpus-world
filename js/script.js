var canvas,			// Canvas DOM element
	ctx,
    keys,
	env,
	isAlive = true,
	isFinished = false,
    player;

function restart(){

    if (!env){
        env = new Environment(15, 8, 64, 64);
    }

    // We need to create a new environment if it is the first time of the player won
    if (isFinished) {
        env = new Environment(15, 8, 64, 64);
    } else {
        env.restart();
    }

    player = new Player(env, 0, 0);

    $("#modal-win").modal("hide");
    $("#modal-game-over").modal("hide");
    $('#btn-remove-walls').prop('checked', false);

    resources.stop("game-over");
    resources.stop("win");
    resources.play("theme", false);

    isAlive = true,
	isFinished = false,

    animate();
}

// Add after environment initialization
function updateStatusIndicators() {
  const dangerLevel = env.wumpus.length > 5 ? 'High' : 'Low';
  const goldProximity = isNearGold() ? 'Gold nearby!' : '';
  
  $('#game-status').html(`
    <div class="alert alert-info">
      <strong>Status:</strong>
      <span>Danger Level: ${dangerLevel}</span>
      <span>${goldProximity}</span>
    </div>
  `);
}

function isNearGold() {
  // Check if gold is in adjacent cells
  // Return true if gold is nearby
}

// Browser window resize
function resizeCanvas(){
	canvas.width = env.width * env.i;
	canvas.height = env.height * env.j;
}

// Keyboard key down
function onKeydown(e) {
	// if (player) {
	// 	keys.onKeyDown(e);
	// };
	keys.onKeyDown(e);

	animate();
};

function update(){
    // Remove the score penalty for movement
    player.update(keys);

    var deadWumpus = player.kill(keys);

    if (deadWumpus) {
        player.score += 1000;
        env.removeWumpus(deadWumpus);
    }

    var capturedGold = player.capture(keys);

    if (capturedGold) {

        player.score += 1000;

        env.removeGold(capturedGold);

        resources.play("gold");

        if (env.golds.length == 0){
            isFinished = true;
        }
    }

    if(env.hasAHole(player) || env.hasAWumpus(player)){
        isAlive = false;
    }

    $("#score").html(player.score);
    $("#arrow").html(player.arrow);
    $("#gold").html(env.golds.length);

    if(!isAlive){
        displayGameOver();
    }

    if(isFinished){
        displayCongratulations();
    }
}

function displayGameOver(){
    $("#modal-game-over").modal("show");
    resources.play("game-over", false);
    resources.stop("theme");
}

function displayCongratulations(){
    $("#modal-win").modal("show");
    resources.play("win", false);
    resources.stop("theme");
}

function draw(){

    // Wipe the canvas clean
	ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (env) {
	    env.draw(ctx);
    }

    if (player) {
	    player.draw(ctx);
    }
}

function animate(){
    update();
	draw();
}

function getURL(){
	var url = "{";

	url += "\"holes\":" + encodeToArray(env.holes) + ",";
	url += "\"golds\":" + encodeToArray(env.golds) + ",";
	url += "\"wumpus\":" + encodeToArray(env.wumpus) + "}";

	return "#" + btoa(url);
}

function encodeToArray(array){
	return JSON.stringify(array);
}

function getLink(){
	return window.location.href+getURL();
}

function loadEnvironment(hash){

    var link = atob(hash.replace('#', ''));

	var obj = $.parseJSON(link);

	env.holes = obj.holes;
	env.golds = obj.golds;
	env.wumpus = obj.wumpus;

	animate();
}

function getCurrentVolume(){
    return localStorage.getItem("wws-volume") || 0.1;
}

function changeVolumeTo(level){

    console.log("Changing volume to", level);

    Howler.volume(level);

    localStorage.setItem("wws-volume", level);
}

function getCurrentLanguage(){
    return localStorage.getItem("wws-locale") || 'en_us';
}

function changeLanguageTo(locale){

    console.log("Changing language to", locale);

    if (locale == "ar") {
        $("html[lang=en]").attr("dir", "rtl")
    } else {
        $("html[lang=en]").attr("dir", "ltr")
    }

    // Define the current language
    $.i18n().locale = locale;
    // Change all text on the webpage
    $('body').i18n();
    // We need to refresh the bootstrap-select
    $('#select-language').selectpicker('refresh');
    // Save the current locate on the locale storage to reload
    localStorage.setItem("wws-locale", locale);
    // We need to redraw the canvas as well
    draw();
}

// Add this near your other initialization code
function checkGestureControls() {
    fetch('http://localhost:5000/get-key')
        .then(response => response.json())
        .then(data => {
            if (data.key) {
                // Simulate key press based on gesture
                switch(data.key) {
                    case 'UP':
                        simulateKeyPress(38); // Up arrow key code
                        break;
                    case 'DOWN':
                        simulateKeyPress(40); // Down arrow key code
                        break;
                    case 'LEFT':
                        simulateKeyPress(37); // Left arrow key code
                        break;
                    case 'RIGHT':
                        simulateKeyPress(39); // Right arrow key code
                        break;
                    case 'ENTER':
                        simulateKeyPress(13); // Enter key code
                        break;
                }
            }
        })
        .catch(error => console.error('Error:', error));
}

function simulateKeyPress(keyCode) {
    // Create and dispatch keydown event
    const keydownEvent = new KeyboardEvent('keydown', {
        keyCode: keyCode,
        which: keyCode,
        bubbles: true
    });
    document.dispatchEvent(keydownEvent);

    // Create and dispatch keyup event
    const keyupEvent = new KeyboardEvent('keyup', {
        keyCode: keyCode,
        which: keyCode,
        bubbles: true
    });
    document.dispatchEvent(keyupEvent);
}

// Start polling for gesture controls
setInterval(checkGestureControls, 100); // Check every 100ms

$(function(){

	console.log("Welcome to Wumpus World Simulator");

    // Declare the canvas and rendering context
	canvas = document.getElementById("canvas");
	ctx = canvas.getContext("2d");
    keys = new Keys();

    // To style all selects
    $('select').selectpicker({
        dropdownAlignRight: true
    });

    $.i18n.debug = true;

    $.i18n({
        locale: getCurrentLanguage()
    });

    $.i18n().load( {
        en_us: 'i18n/en_us.json',
        pt_br: 'i18n/pt_br.json',
        ar: 'i18n/ar.json',
        fr: 'i18n/fr.json',
        tr_TR: 'i18n/tr_TR.json'
    }).done( function() {
        changeLanguageTo($.i18n().locale);
    });

    $('#select-language').selectpicker('val', $.i18n().locale);

	$("#select-language").change(function(event){
        event.preventDefault();
        changeLanguageTo($(this).val());
	});

    $('#btn-remove-walls').change(function() {
        env.removeWalls = this.checked;
        // Remove focus
        $(this).blur();
        animate();
    });

    $(".btn-restart").click(function(){
		restart();
	});

	$(".card-game").width(canvas.width);
	$(".card-game .card-content").height(canvas.height);

	$('#modal-share').on('shown.bs.modal', function () {
		$('#textarea-link').text(getLink());
	});

    changeVolumeTo(getCurrentVolume());

    $("#btn-volume").val(getCurrentVolume().toString());

    $("#btn-volume").change(function(event){
        event.preventDefault();
        changeVolumeTo($(this).val());
    });

    if (!localStorage.getItem('tutorialSeen')) {
        $('#tutorial-modal').modal('show');
        localStorage.setItem('tutorialSeen', true);
    }

    resources.load().then(() => {

        resources.play("theme", false);

        var hash = window.location.hash;

		if (hash) {
			loadEnvironment(hash);
		}

        restart();

        resizeCanvas();

        // Start listening for events
        window.addEventListener("keydown", onKeydown, false);

		animate();
    })
});
