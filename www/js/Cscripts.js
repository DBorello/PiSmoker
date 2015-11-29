//Setup Controls plot
var u = [];
var P = [];
var I = [];
var D = [];
function CUpdatePlot() {
		var Cdataset = [
			{
				label: "u",
				data: u,
				color: "#FF0000",
				points: { fillColor: "#FF0000", show: false },
				lines: { show: true }
			},
			{
				label: "P",
				data: P,
				color: "#ff3399",
				points: { fillColor: "#ff3399", show: false },
				lines: { show: true }
			},
			{
				label: "I",
				data: I,
				color: "#0062E3",
				points: { fillColor: "#0062E3", show: false },
				lines: { show: true }
			},
			{
				label: "D",
				data: D,
				color: "#003300",
				points: { fillColor: "#003300", show: false },
				lines: { show: true }
			}
		]	
			
		var Coptions = {
			series: {
				shadowSize: 5
			},
			xaxes: [
			{
				mode: "time",
				timeformat: "%H:%M",
				tickSize: [15, "minute"],
				timezone: "browser",
				color: "black",        
				axisLabel: "Date",
				axisLabelUseCanvas: true,
				axisLabelFontSizePixels: 12,
				axisLabelFontFamily: 'Verdana, Arial',
				axisLabelPadding: 10
			}],
			yaxis: {        
				color: "black",
				tickDecimals: 1,
				axisLabel: "",
				axisLabelUseCanvas: true,
				axisLabelFontSizePixels: 12,
				axisLabelFontFamily: 'Verdana, Arial',
				axisLabelPadding: 6,
				min: -1,
				max: 1
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
		
		$.plot($("#controls-placeholder"), Cdataset, Coptions);
		$("#controls-placeholder").UseTooltip();

}


//Firebase	
var ControlsRef = Ref.child('Controls');


ControlsRef.once("value", function(snapshot) {
	var Controls = snapshot.val();
	for (var k in Controls) {
		u.push([Controls[k].time, Controls[k].u]);
		P.push([Controls[k].time, Controls[k].P]);
		I.push([Controls[k].time, Controls[k].I]);
		D.push([Controls[k].time, Controls[k].D]);
	}
	ControlsRef.limitToLast(1).on("child_added", function(snapshot, prevChildKey) { //Establish callback
		var Controls = snapshot.val();
		u.push([Controls.time, Controls.u]);
		P.push([Controls.time, Controls.P]);
		I.push([Controls.time, Controls.I]);
		D.push([Controls.time, Controls.D]);
		CUpdatePlot()
		
	});
});
ControlsRef.on("child_removed", function(snapshot, prevChildKey) {
	u = [];
	P = [];
	I = [];
	D = []; 
	CUpdatePlot()
});
