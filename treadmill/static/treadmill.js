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
// change parameters in config json file
app.controller('configFormController', function($scope, $rootScope, $http, statusFactory) {

    $rootScope.$on("CallParentMethod", function() {
        //console.log('in CallParentMethod:')
        $scope.getPromise();
    });

    /*
    $scope.submitAnimalForm = function() {
        console.log('submitAnimalForm()', $scope.configData, 'valid:', $scope.configData.$valid);
        url = $scope.myUrl + 'api/submit/configparams'
        console.log('$scope.configData:', $scope.configData.trial.config)
        $http.post(url, JSON.stringify($scope.configData.trial.config)).
        	then(function(response) {
        		//console.log('response.data:', response.data)
        	});
    };
    */
    
    $scope.submitConfigForm = function() {
        console.log('submitConfigForm()', $scope.configData, $scope.configData.$valid);
        url = $scope.myUrl + 'api/submit/configparams'
        console.log('$scope.configData:', $scope.configData.trial.config)
        $http.post(url, JSON.stringify($scope.configData.trial.config)).
        	then(function(response) {
        		//console.log('response.data:', response.data)
        	});
    };
    
    $scope.submitAnimalForm = function() {
        console.log('submitConfigForm()', $scope.configData, $scope.configData.$valid);
        url = $scope.myUrl + 'api/submit/animalparams'
        console.log('$scope.configData:', $scope.configData.trial.config)
        $http.post(url, JSON.stringify($scope.configData.trial.config)).
        	then(function(response) {
        		//console.log('response.data:', response.data)
        		//$scope.configData = response.data
        	});
    };
    
    $scope.saveConfig = function() {
        //console.log('saveConfig()', $scope.configData, $scope.configData.$valid);
        url = $scope.myUrl + 'api/submit/saveconfig'
        //console.log('$scope.configData:', $scope.configData.trial.config)
        $http.get(url).
        	then(function(response) {
        		//console.log('response.data:', response.data)
        	});
    };
    

    $scope.animalParamChange = function(isValid) {
    	// if form fields don't pass validation, they will be 'undefined'
    	console.log('animalParamChange()', 'isValid:', isValid, $scope.configData)
    	if (isValid) {
    		$scope.submitAnimalForm()
    	}
    }
    
    $scope.configParamChange = function(isValid) {
    	// if form fields don't pass validation, they will be 'undefined'
    	console.log('configParamChange()', 'isValid:', isValid, $scope.configData)
    	if (isValid) {
    		$scope.submitConfigForm()
    	}
    }
    
	$scope.getPromise = function() {
		console.log('getPromise')
		var  myPromise = statusFactory.getStatus()
    	myPromise.then(function(result) {
			// this is a large layered dictionary, only change:
			// status.trial.config.lights
			// status.trial.config.trial
			// status.trial.config.video
			$scope.configData = result				
    		
    		//$scope.userSerial = trial.config.hardware.serial.useSerial
    		//$scope.allowArming = $scope.configData.trial.config.hardware.allowArming
    		
    		console.log('configFormController $scope.configData:', $scope.configData)
    	},
    	function(data) {
    	    // Handle error here
    	    console.log('configFormController error in myPromise')
		}); // mypromise.then
	}
	
	console.log('1')
	$scope.getPromise()
	
}); // configFormController


//////////////////////////////////////////////////////////////////////////////
app.controller('arduinoFormController', function($scope, $rootScope, $http, statusFactory) {
    
    $scope.submitForm = function() {
        console.log("posting data....", $scope.data, $scope.data.$valid);
        url = $scope.myUrl + 'api/submit/motorparams'
        $http.post(url, JSON.stringify($scope.data)).
        	then(function(response) {
        		//console.log('response.data:', response.data)
			    //I need to do this to update configFormController configData
			    // call the other controller with this
			    $rootScope.$emit("CallParentMethod", {});
        	});
    };
    
    $scope.motorParamChange = function() {
    	// if form fields don't pass validation, they will be 'undefined'
    	console.log('motorParamChange()', $scope.data)
    	buildPlotly($scope.data)
    }
    
    var myPromise = statusFactory.getStatus()
    myPromise.then(function(result) {
    	var status = result
    	console.log('arduinoFormController myPromise:', status)

		// motorParams
		// remember, repeatDuration is in seconds, repeatduration is in ms
		// todo: clean up numberofrepeats versus numberOfRepeats
		$scope.data = {
			
			motorNumberofRepeats: status.trial.config.motor.motorNumberofRepeats,
			motorRepeatDuration: status.trial.config.motor.motorRepeatDuration,
			motorDel: status.trial.config.motor.motorDel,
			motorDur: status.trial.config.motor.motorDur,
			motorSpeed: status.trial.config.motor.motorSpeed,
			motorDirection: status.trial.config.motor.motorDirection
		};
		
		//console.log('$scope.data:', $scope.data)
		//console.log('delay:', status.motor.motorDel)
		//console.log('numberOfRepeats:', status.trial.config.trial.numberOfRepeats)
		//console.log('repeatDuration:', status.trial.config.trial.repeatDuration)
		
		buildPlotly($scope.data)
		
	}); // mypromise.then

	var buildPlotly = function(motorParams){
		var trialMS = motorParams.motorNumberofRepeats * motorParams.motorRepeatDuration
		//console.log('buildPlotly() trialMS:', trialMS)
		//console.log('buildPlotly() motorParams:', motorParams)
		
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
		
		// make a list of rect shapes, one per repeat
		var i
		var shapeList = []
		for (i=0; i<motorParams.motorNumberofRepeats; i++) {
			thisStart = motorParams.motorRepeatDuration * i + motorParams.motorDel
			thisStop = thisStart + motorParams.motorDur
			thisRect = {
				'type': 'rect',
				'x0': thisStart,
				'y0': 0,
				'x1': thisStop,
				'y1': 1,
				'line': {
					'color': lineColor,
				},
				'fillcolor': lineColor,
			};
			shapeList.push(thisRect)
		}
		
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
		'shapes': shapeList,
		};
		
		var config = {
    	    'displayModeBar': false
	    }

		Plotly.plot(gd, data, layout, config)
		// todo: seperate new lpot from update plot
		// this is for when we update
		Plotly.react(gd, data, layout, config)
		
		window.onresize = function() {
			Plotly.Plots.resize('test_plotly');
		};

	}; // $scope.buildPlotly
}); // arduinoFormController

//////////////////////////////////////////////////////////////////////////////
app.controller('treadmill', function($scope, $rootScope, $window, $http, $location, $interval, $sce, $timeout, $document) {
	
	console.log('angular.version:', angular.version)
	
	//url of page we loaded
	$scope.myUrl = $location.absUrl(); //with port :5000

    myStreamUrl = 'http://' + $location.host() + ':8080/stream';
    $scope.myStreamUrl0 = myStreamUrl
    $scope.myStreamUrl = $sce.trustAsResourceUrl(myStreamUrl);
	
	$scope.showConfigTable = false;
	$scope.showConfig = true;
	$scope.showMotor = false;
	//$scope.allowArming = false
	
    //read the state from homecage backend, do this at an interval
    $scope.getStatus = function () {
		$http.get($scope.myUrl + 'status').
        	then(function(response) {
        	    $scope.status = response.data;
				// for armed checkbox, it needs a model
				$scope.isArmed = $scope.isState('armed') || $scope.isState('armedrecording')
				//for streaming
				var tmpWidth = parseInt($scope.status.trial.config.video.streamResolution.split(',')[0],10)
				var tmpHeight = parseInt($scope.status.trial.config.video.streamResolution.split(',')[1],10)
				$scope.streamWidth = tmpWidth + (tmpWidth * 0.04)
				$scope.streamHeight = tmpHeight + (tmpWidth * 0.04)

        	});
	};

    // mixing controllers, this submits main $scope.config
    $scope.submitLEDForm = function() {
        console.log('submitLEDForm() $scope.status.trial.config:', $scope.status.trial.config.hardware.eventOut);
        url = $scope.myUrl + 'api/submit/ledparams'
        $http.post(url, JSON.stringify($scope.status.trial.config)).
        	then(function(response) {
        		$scope.status = response.data
        		console.log('$scope.status:', $scope.status)
        		//$scope.$apply();
        	});
    };
    

	// one button callback
	$scope.buttonCallback = function(buttonID) {
		console.log('buttonCallback() buttonID=', buttonID)
		switch (buttonID) {
			case 'toggleConfig':
				$scope.showConfig = ! $scope.showConfig
				break;
			case 'toggleMotor':
				$scope.showMotor = ! $scope.showMotor
				break;
			case 'toggleConfigTable':
				$scope.showConfigTable = ! $scope.showConfigTable
				break;
				
			case 'startRecord':
				url = $scope.myUrl + 'startRecord'
				$http.get(url).
    		    		then(function(response) {
        				    $scope.status = response.data;
        				});
				break;
			case 'stopRecord':
				url = $scope.myUrl + 'stopRecord'
				$http.get(url).
    		    		then(function(response) {
        				    $scope.status = response.data;
        				});
				break;

			case 'startStream':
				url = $scope.myUrl + 'startStream'
				$http.get(url).
    		    		then(function(response) {
        				    $scope.status = response.data;
        				});
				break;
			case 'stopStream':
				url = $scope.myUrl + 'stopStream'
				$http.get(url).
    		    		then(function(response) {
        				    $scope.status = response.data;
        				});
				break;

			case 'toggleArm':
				if ($scope.isState('armed')) {
					url = $scope.myUrl + 'stopArm'
					$http.get(url).
							then(function(response) {
								$scope.status = response.data;
							});
				} else if ($scope.isState('idle')) { //safety check, index interface should handle
					url = $scope.myUrl + 'startArm'
					$http.get(url).
							then(function(response) {
								$scope.status = response.data;
								$rootScope.$emit("CallParentMethod", {});
							});
				}
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

			/*
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
			*/
			
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
	
	$scope.allowParamEdit = function() {
		return $scope.isState('idle')
	}
	
	$interval($scope.getStatus, 400); // no () in function call !!!	


}); // treadmill controller
