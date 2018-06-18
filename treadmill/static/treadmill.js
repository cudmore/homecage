var app = angular.module('demo', ['uiSwitch']);

//////////////////////////////////////////////////////////////////////////////
app.factory('statusFactory', function($http, $location, $interval) {
	var myUrl = $location.absUrl(); //with port :5000
	var getStatus = function () {
		var url = myUrl + 'status'
		return $http.get(url).
        	then(function(response) {
				//console.log('statusFactory status=', response.data)
				return response.data
        	});
    };
    return {getStatus: getStatus}
});

//////////////////////////////////////////////////////////////////////////////
app.controller('arduinoFormController', function($scope, $http, statusFactory) {
    
    $scope.submitForm = function() {
        console.log("posting data....", $scope.data, $scope.data.$valid);
        url = $scope.myUrl + 'api/submit/motorparams'
        $http.post(url, JSON.stringify($scope.data)).
        	then(function(response) {
        		//console.log('response.data:', response.data)
        	});
    };
    
    myPromise = statusFactory.getStatus()
    myPromise.then(function(result) {
    	$scope.status = result
    	//console.log('xxx:', $scope.status)

		$scope.data = {
			numberofrepeats: 3,
			repeatduration: 20000,
			motorDelay: $scope.status.trial.trial.motor.delay,
			motorDuration: $scope.status.trial.trial.motor.duration,
			motorSpeed: $scope.status.trial.trial.motor.speed,
			motorDirection: $scope.status.trial.trial.motor.direction
		};
		//console.log('$scope.data:', $scope.data)
		//console.log('delay:', $scope.status.trial.trial.motor.delay)
		console.log('numberOfRepeats:', $scope.status.trial.config.video.numberOfRepeats)
		console.log('fileDuration:', $scope.status.trial.config.video.fileDuration)

		var trialMS = $scope.data.numberofrepeats * $scope.data.repeatduration
		
		//
		// plotly
		var d3 = Plotly.d3;
		var WIDTH_IN_PERCENT_OF_PARENT = 100
		var HEIGHT_IN_PERCENT_OF_PARENT = 12;

		  var gd3 = d3.select("#test_plotly")
			  .style({
				width: WIDTH_IN_PERCENT_OF_PARENT + '%',
				//'margin-left': (100 - WIDTH_IN_PERCENT_OF_PARENT) / 2 + '%',
		
				height: HEIGHT_IN_PERCENT_OF_PARENT + 'vh',
				//'margin-top': (100 - HEIGHT_IN_PERCENT_OF_PARENT) / 2 + 'vh'
			  });

		var gd = gd3.node();

		var data = [
		  {
			x: [],
			y: [],
			type: 'scatter'
		  }
		];

		var lineColor = 'rgba(100,100,100,1)'
		
		var layout = {
		  showlegend: false,
		  margin: {
			l: 25,
			t: 25,
			r: 25,
			b: 40,
			pad: 4,
		  },
		  'xaxis': {
		  	'range': [0, trialMS],
		  	'zeroline': false,
		  	'title': 'ms'
		  },
		  'yaxis': {
		  	'showticklabels': false,
		  	//'zeroline': false,
		  	'showline': false,
		  	'showgrid': false,
		  	'ticks': '',
		  	'showticklabels': false,
		  	'range': [0, 1],
		  },
		  //paper_bgcolor: '#7f7f7f',
		  //plot_bgcolor: '#c7c7c7',
		'shapes': [
			{
				'type': 'rect',
				'x0': 7000,
				'y0': 0,
				'x1': 7000+7000,
				'y1': 1,
				'line': {
					'color': lineColor,
				},
				'fillcolor': lineColor,
			},
			{
				'type': 'rect',
				'x0': 20000+7000,
				'y0': 0,
				'x1': 20000+7000+7000,
				'y1': 1,
				'line': {
					'color': lineColor,
					'width': 2,
				},
				'fillcolor': lineColor,
			},
		]
		};
		
		var config = {
    	    'displayModeBar': false
	    }

		Plotly.plot(gd, data, layout, config)
				window.onresize = function() {
					Plotly.Plots.resize('test_plotly');
				};

			});
		});

//////////////////////////////////////////////////////////////////////////////
app.controller('treadmill', function($scope, $window, $http, $location, $interval, $sce, $timeout, $document) {
	
	console.log('angular.version:', angular.version)
	
	//url of page we loaded
	$scope.myUrl = $location.absUrl(); //with port :5000
	console.log('$scope.myUrl=', $scope.myUrl)
	
	$scope.showConfig = false;
	
    //read the state from homecage backend, do this at an interval
    $scope.getStatus = function () {
		$http.get($scope.myUrl + 'status').
        	then(function(response) {
        	    $scope.status = response.data;
				//console.log('$scope.status=', $scope.status)
        	});
	};

	// one button callback
	$scope.buttonCallback = function(buttonID) {
		console.log('buttonCallback() buttonID=', buttonID)
		switch (buttonID) {
			case 'toggleConfig':
				$scope.showConfig = ! $scope.showConfig
				break;
				
			case 'startTrial':
				url = $scope.myUrl + 'startTrial'
				$http.get(url).
    		    		then(function(response) {
        				    $scope.status = response.data;
        				});
				break;
			case 'stopTrial':
				url = $scope.myUrl + 'stopTrial'
				$http.get(url).
    		    		then(function(response) {
        				    $scope.status = response.data;
        				});
				break;

			case 'startArm':
				url = $scope.myUrl + 'startArm'
				$http.get(url).
    		    		then(function(response) {
        				    $scope.status = response.data;
        				});
				break;
			case 'stopArm':
				url = $scope.myUrl + 'stopArm'
				$http.get(url).
    		    		then(function(response) {
        				    $scope.status = response.data;
        				});
				break;

			default:
				console.log('buttonCallback() case not taken, buttonID=',buttonID);
				break;
		}
	}
	
	$scope.isState = function(state) {
		if ($scope.status) {
			return $scope.status.trial.trial.cameraState == state
		} else {
			return ''
		}
	}
		
	$interval($scope.getStatus, 1000); // no () in function call !!!	


}); // treadmill controller
