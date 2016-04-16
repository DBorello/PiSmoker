//Setup temperature plot
var T1 = [];
var T2 = [];
var TT = [];
function UpdatePlot() {
		var dataset = [
			{
				label: "Grill",
				data: T1,
				color: "#FF0000",
				points: { fillColor: "#FF0000", show: false },
				lines: { show: true }
			},
			{
				label: "Meat",
				data: T2,
				color: "#0062E3",
				points: { fillColor: "#0062E3", show: false },
				lines: { show: true }
			},
			{
				label: "Target",
				data: TT,
				color: "#003300",
				points: { fillColor: "#003300", show: false },
				lines: { show: true }
			}
		]	
			
		var options = {
			series: {
				shadowSize: 5
			},
			xaxes: [
			{
				mode: "time",
				timeformat: "%H:%M",
				//tickSize: [15, "minute"],
				minTickSize: [1, "minute"],
				timezone: "browser",
				color: "black",        
				axisLabel: "Date",
				axisLabelUseCanvas: true,
				axisLabelFontSizePixels: 16,
				axisLabelFontFamily: 'Verdana, Arial',
				axisLabelPadding: 10
			}],
			yaxis: {        
				color: "black",
				tickDecimals: 1,
				axisLabel: "Temp (F)",
				axisLabelUseCanvas: true,
				axisLabelFontSizePixels: 16,
				axisLabelFontFamily: 'Verdana, Arial',
				axisLabelPadding: 6
			},
			legend: {
				noColumns: 0,
				labelFormatter: function (label, series) {
					return "<font color=\\\"white\\\">" + label + "</font>";
				},
				backgroundColor: "#000",
				backgroundOpacity: 0.1,
				labelBoxBorderColor: "#000000",
				position: "sw"
			},
			grid: {
				hoverable: true,
				borderWidth: 3,
				mouseActiveRadius: 50,
				backgroundColor: { colors: ["#ffffff", "#EDF5FF"] },
				axisMargin: 20,
				clickable: true
			}
		};
		
		$.plot($("#temp-placeholder"), dataset, options);
		$("#temp-placeholder").UseTooltip();

		//Update gauges
		if (T1.length > 0) {
			gG.refresh(T1[T1.length-1][1]);
			gM.refresh(T2[T2.length-1][1]);
		}
}

var previousPoint = null, previousLabel = null;
var monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

$.fn.UseTooltip = function () {
	$(this).bind("plothover", function (event, pos, item) {
		if (item) {
			if ((previousLabel != item.series.label) || (previousPoint != item.dataIndex)) {
				previousPoint = item.dataIndex;
				previousLabel = item.series.label;
				$("#tooltip").remove();
				
				var x = item.datapoint[0];
				var y = item.datapoint[1];
				var date = new Date(x);
				var color = item.series.color;

				showTooltip(item.pageX, item.pageY, color,
							"<strong>" + item.series.label + "</strong><br>"  +
							(date.getHours()) + ":" + date.getMinutes() +
							" : <strong>" + Math.round(y) + "</strong> F");
			}
		} else {
			$("#tooltip").remove();
			previousPoint = null;
		}
	});
};

function showTooltip(x, y, color, contents) {
	$('<div id="tooltip">' + contents + '</div>').css({
		position: 'absolute',
		display: 'none',
		top: y - 40,
		left: x - 120,
		border: '2px solid ' + color,
		padding: '3px',
		'font-size': '9px',
		'border-radius': '5px',
		'background-color': '#fff',
		'font-family': 'Verdana, Arial, Helvetica, Tahoma, sans-serif',
		opacity: 0.9
	}).appendTo("body").fadeIn(200);
}

//Setup Gages
var gG = new JustGage({
	id: "GrillGauge",
	value: 0,
	min: 0,
	max: 500,
	title: "Grill",
	label: "F",
	levelColorsGradient: false,
	decimals: 1
});

var gM = new JustGage({
	id: "MeatGauge",
	value: 00,
	min: 0,
	max: 200,
	title: "Meat",
	label: "F",
	levelColorsGradient: false,
	decimals: 1
});


//Firebase	
var Ref = new Firebase('https://pismoker.firebaseio.com/');
var TempsRef = Ref.child('Temps');
var ParametersRef = Ref.child('Parameters');
var ProgramRef = Ref.child('Program');

TempsRef.once("value", function(snapshot) {
	var Ts = snapshot.val();
	for (var k in Ts) {
		T1.push([Ts[k].time, Ts[k].T1]);
		T2.push([Ts[k].time, Ts[k].T2]);
		TT.push([Ts[k].time, Ts[k].TT]);
	}
	TempsRef.limitToLast(1).on("child_added", function(snapshot, prevChildKey) { //Establish callback
		var Ts = snapshot.val();
		T1.push([Ts.time, Ts.T1])
		T2.push([Ts.time, Ts.T2])
		TT.push([Ts.time, Ts.TT])
		UpdatePlot()
	});
});
TempsRef.on("child_removed", function(snapshot, prevChildKey) {
  T1 = []
  T2 = []
  TT = []  
  UpdatePlot()
});



function clearData() {
	TempsRef.remove();
	ControlsRef.remove();
}


document.getElementById('ControlsRow').style.display = 'none'