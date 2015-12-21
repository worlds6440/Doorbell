function init() {
ns4 = (document.layers)?true:false;
ie4 = (document.all)?true:false;
sliderMin = 50;
sliderMax = 306;
rValue=0;
gValue=0;
bValue=0;
r1 = '0';
r2 = '0';
g1 = '0';
g2 = '0';
b1 = '0';
b2 = '0';
Rgb = '0';
rGb = '0';
rgB = '0';
rActive = false;
gActive = false;
bActive = false;
document.onmousedown = mouseDown
document.onmousemove = mouseMove
document.onmouseup = mouseUp
if (ns4) document.captureEvents(Event.MOUSEDOWN | Event.MOUSEMOVE | Event.MOUSEUP);
if (ns4) {
domRed = document.redSlider;
domRed.xpos = parseInt(domRed.left);
domRed.ypos = parseInt(domRed.top);
domRed.w = domRed.clip.width;
domRed.h = domRed.clip.height;
domGreen = document.greenSlider;
domGreen.xpos = parseInt(domGreen.left);
domGreen.ypos = parseInt(domGreen.top);
domGreen.w = domGreen.clip.width;
domGreen.h = domGreen.clip.height;
domBlue = document.blueSlider;
domBlue.xpos = parseInt(domBlue.left);
domBlue.ypos = parseInt(domBlue.top);
domBlue.w = domBlue.clip.width;
domBlue.h = domBlue.clip.height;
domDisplay = document.display;
domValue = document.hexValue.document.frmValue.valueDisp;
domredValue = document.hexValue.document.frmValue.RgbDisp;
domgreenValue = document.hexValue.document.frmValue.rGbDisp;
domblueValue = document.hexValue.document.frmValue.rgBDisp;
}
else {
domRed = redSlider.style;
domRed.xpos = redSlider.offsetLeft;
domRed.ypos = redSlider.offsetTop;
domRed.w = redSlider.clientWidth;
domRed.h = redSlider.clientHeight;
domGreen = greenSlider.style;
domGreen.xpos = greenSlider.offsetLeft;
domGreen.ypos = greenSlider.offsetTop;
domGreen.w = greenSlider.clientWidth;
domGreen.h = greenSlider.clientHeight;

domBlue = blueSlider.style;
domBlue.xpos = blueSlider.offsetLeft;
domBlue.ypos = blueSlider.offsetTop;
domBlue.w = blueSlider.clientWidth;
domBlue.h = blueSlider.clientHeight;
domDisplay = display;
domValue = frmValue.valueDisp;
domredValue = frmValue.RgbDisp;
domgreenValue = frmValue.rGbDisp;
domblueValue = frmValue.rgBDisp;
}
hexArray = new Array('0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F');
}
function mouseDown(e) {
if ((ns4 && e.which!=1) || (ie4 && event.button!=1)) return true;
var x = (ns4)? e.pageX : event.x+document.body.scrollLeft;
var y = (ns4)? e.pageY : event.y+document.body.scrollTop;
if (x > domRed.xpos && x < domRed.xpos+domRed.w && y > domRed.ypos && y < domRed.ypos+domRed.h){ rActive = true; dragObject = domRed; }
if (x > domGreen.xpos && x < domGreen.xpos+domGreen.w && y > domGreen.ypos && y < domGreen.ypos+domGreen.h){ gActive = true; dragObject = domGreen; }
if (x > domBlue.xpos && x < domBlue.xpos+domBlue.w && y > domBlue.ypos && y < domBlue.ypos+domBlue.h){ bActive = true; dragObject = domBlue; }
if (rActive==true || gActive==true || bActive==true){
if (x>=dragObject.xpos && x<=dragObject.xpos+dragObject.w) {
dragObject.dragOffsetX = x-dragObject.xpos
}
return false
}
else {
return true
   }
}
function mouseMove(e) {
var x = (ns4)? e.pageX : event.x+document.body.scrollLeft;
var y = (ns4)? e.pageY : event.y+document.body.scrollTop;
if (rActive) {
rMoveTo = x-dragObject.dragOffsetX;
if (rMoveTo > sliderMax) rMoveTo = 306;
if (rMoveTo < sliderMin) rMoveTo = 50;
domRed.xpos = rMoveTo;
domRed.left = domRed.xpos;
rValue = (domRed.xpos+4)-50;
calcValue(rMoveTo-50, 'red');
}
if (gActive) {
gMoveTo = x-dragObject.dragOffsetX;
if (gMoveTo > sliderMax) gMoveTo = sliderMax;
if (gMoveTo < sliderMin) gMoveTo = sliderMin;
domGreen.xpos = gMoveTo;
domGreen.left = domGreen.xpos;
gValue = (domGreen.xpos+4)-50;
calcValue(gMoveTo-50, 'green');
}
if (bActive) {
bMoveTo = x-dragObject.dragOffsetX;
if (bMoveTo > sliderMax) bMoveTo = sliderMax;
if (bMoveTo < sliderMin) bMoveTo = sliderMin;
domBlue.xpos = bMoveTo;
domBlue.left = domBlue.xpos;
bValue = (domBlue.xpos+4)-50;
calcValue(bMoveTo-50, 'blue');
}
return true
}
function mouseUp(e) {
var x = (ns4)? e.pageX : event.x+document.body.scrollLeft
var y = (ns4)? e.pageY : event.y+document.body.scrollTop
rActive = false;
gActive = false;
bActive = false;
return true
}
function calcValue(base, color) {
base -= 1;
if (base < 16) { first = 0; }
else { first = parseInt(base/16); }
if (base < 0 ) { second = 0; base = 0; }
else { second = parseInt(base%16); }
c1=hexArray[first];
c2=hexArray[second];
if (color == 'red') { r1 = c1; r2 = c2; Rgb=base; }
else if (color == 'green') { g1 = c1; g2 = c2; rGb=base; }
else { b1 = c1; b2 = c2; rgB=base; }
domValue.value = eval('"'+r1+r2+g1+g2+b1+b2+'"');
domredValue.value = eval('"'+Rgb+'"');
domgreenValue.value = eval('"'+rGb+'"');
domblueValue.value = eval('"'+rgB+'"');
if (ns4) { domDisplay.bgColor = eval('"#'+r1+r2+g1+g2+b1+b2+'"'); }
else { domDisplay.style.backgroundColor = eval('"#'+r1+r2+g1+g2+b1+b2+'"'); }
return true;
}
function manualSet(value,color) {
if (value < 0) value=0;
if (value > 255) value=255;
++value;
calcValue(value,color);
if (color == 'red'){ domRed.xpos = value+sliderMin-4; domRed.left = domRed.xpos; }
else if (color == 'green'){ domGreen.xpos = value+sliderMin-4; domGreen.left = domGreen.xpos; }
else { domBlue.xpos = value+sliderMin-4; domBlue.left = domBlue.xpos; }
}
function convertHex(hexString) {
if(hexString == null) hexString = domValue.value;
inputHexArray = new Array(6);
for(i=0;i<=5;++i) {
inputHexArray[i] = hexString.charAt(i);
}
for(i=0;i<=5;++i) {
tempHexVal = inputHexArray[i];
for(j=0;j<=15;++j) {
if(tempHexVal == hexArray[j]) tempHexVal = j;
}
inputHexArray[i] = tempHexVal;
}
Rgb = (inputHexArray[0]*16)+inputHexArray[1]+1;
calcValue(Rgb,'red');
manualSet(Rgb,'red');
rGb = (inputHexArray[2]*16)+inputHexArray[3]+1;
calcValue(rGb,'green');
manualSet(rGb,'green');
rgB = (inputHexArray[4]*16)+inputHexArray[5]+1;
calcValue(rgB,'blue');
manualSet(rgB,'blue');
}
