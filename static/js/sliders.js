function init() {
	ns4 = (document.layers)?true:false;
	ie4 = (document.all)?true:false;
	m_redValue = 0;
	m_greenValue = 0;
	m_blueValue = 0;

	// Pull RGB values from initial input values
	var rededit = document.getElementById('idred');
	m_redValue = rededit.value;
	var greenedit = document.getElementById('idgreen');
	m_greenValue = greenedit.value;
	var blueedit = document.getElementById('idblue');
	m_blueValue = blueedit.value;

	// Update all edit/slider windows to show initial values
	updateSliders();
	updateRGBEdits();
	updateHexEdit();
	updateDisplay();
}

function updateSliders()
{
	// Ensure sliders are moved to correct positions
	var redslider = document.getElementById("idredslider");
	redslider.value = m_redValue;
	var greenslider = document.getElementById('idgreenslider');
	greenslider.value = m_greenValue;
	var blueslider = document.getElementById('idblueslider');
	blueslider.value = m_blueValue;
}

function updateRGBEdits()
{
	// Ensure RGB edits have correct values
	var rededit = document.getElementById('idred');
	rededit.value = m_redValue;
	var greenedit = document.getElementById('idgreen');
	greenedit.value = m_greenValue;
	var blueedit = document.getElementById('idblue');
	blueedit.value = m_blueValue;
}

function updateHexEdit()
{
	// Ensure Hex edit has correct value
	var hexinput = document.getElementById('idhex');
	hexinput.value = rgb2hex(m_redValue, m_greenValue, m_blueValue);
}

function updateDisplay() {
	// Ensure colour display has correct colour
	
	// Convert R, G and B values into a single hex colour
	var domDisplay = document.getElementById("display");
	var hexValue = rgb2hex(m_redValue, m_greenValue, m_blueValue);

	// Push new hex colour into colour display
	if (ns4) {
		domDisplay.bgColor = hexValue;
	}
	else {
		domDisplay.style.backgroundColor = hexValue;
	}
	return true;
}

function rgb2hex(red, green, blue){
	// Convert RGB values into single Hex colour
	return "#" +
		("0" + Number(red).toString(16)).slice(-2) +
		("0" + Number(green).toString(16)).slice(-2) +
		("0" + Number(blue).toString(16)).slice(-2);
}

function changedSlider(colour, value)
{
	// Ensure value is within reasonable bounds
	if (Number(value) < 0)
		value="0";
	if (Number(value) > 255)
		value="255";

	if (colour == 'red')
	{
		// Changed red slider
		m_redValue = value;
	}
	else if (colour == 'green')
	{
		// Changed green slider
		m_greenValue = value;
	}
	else if (colour == 'blue')
	{
		// Changed blue slider
		m_blueValue = value;
	}
	
	// Update Hex value
	updateHexEdit();
	// update RGB edit boxes
	updateRGBEdits();
	// update colour display
	updateDisplay();
}

function changedHex(value)
{
	// User has changed the hex value, update slider positions
	var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(value);
	m_redValue = parseInt(result[1], 16),
	m_greenValue = parseInt(result[2], 16),
	m_blueValue = parseInt(result[3], 16),

	// Update Slider Positions
	updateSliders();
	// update RGB edit boxes
	updateRGBEdits();
	// update colour display
	updateDisplay();
}

function changedRGBEdits(colour, value)
{
	// Ensure value is within reasonable bounds
	if (Number(value) < 0)
		value="0";
	if (Number(value) > 255)
		value="255";

	if (colour == 'red')
	{
		// Changed red edit
		m_redValue = value;
	}
	else if (colour == 'green')
	{
		// Changed green edit
		m_greenValue = value;
	}
	else if (colour == 'blue')
	{
		// Changed blue edit
		m_blueValue = value;
	}
	
	// Update Slider Positions
	updateSliders();
	// Update Hex value
	updateHexEdit();
	// update colour display
	updateDisplay();
}