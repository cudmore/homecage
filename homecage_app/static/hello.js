
angular.module('demo', ['uiSwitch'])
.controller('Hello', function($scope, $window, $http, $location, $interval, $sce, $timeout, $document) {
	
	console.log('angular.version:', angular.version)
	
	//url of page we loaded
	$scope.myUrl = $location.absUrl(); //with port :5000
	
    myStreamUrl = 'http://' + $location.host() + ':8080/stream';
    $scope.myStreamUrl0 = myStreamUrl
    $scope.myStreamUrl = $sce.trustAsResourceUrl(myStreamUrl);
	
	// title in browser tab
	$document[0].title = "Homecage " + $location.host()
	
	//todo: rewrite these to just be inline with logic in button html
	$scope.showOptions = false;
	$scope.toggleOptions = function() {
		console.log('toggleOptions()')
		$scope.showOptions = ($scope.showOptions === false) ? true: false;
	};

	$scope.showStatus = false;
	$scope.toggleStatus = function() {
		console.log('toggleStatus()')
		$scope.showStatus = $scope.showStatus === false ? true: false;
	};

	$scope.showStill = false;
	$scope.toggleStill = function() {
		console.log('toggleStill()')
		$scope.showStill = $scope.showStill === false ? true: false;
	};

    //read the state from homecage backend, do this at an interval
    $scope.getStatus = function () {
		$http.get($scope.myUrl + 'status').
        	then(function(response) {
        	    $scope.status = response.data;
        	    //
        	    // remove video file list from $scope.status
        	    //$scope.videofilelist = $scope.status.videofilelist
        	    //$scope.status.videofilelist = ''
        	    
        	});
	};

    //read user editable options
    $scope.getConfig = function () {
		$http.get($scope.myUrl + 'config').
        	then(function(response) {
        	    $scope.config = response.data;
        	    convertConfig()
        	    console.log('$scope.config', $scope.config)
        	});
	};

	function convertConfig() {
	    //calculate web page iframe for stream
	    // scope.config.stream.resolution is a string like "1024,768"
		var tmpWidth = parseInt($scope.config.video.streamResolution.split(',')[0],10)
		var tmpHeight = parseInt($scope.config.video.streamResolution.split(',')[1],10)
		$scope.streamWidth = tmpWidth + (tmpWidth * 0.03)
		$scope.streamHeight = tmpHeight + (tmpWidth * 0.03)
	}
	
	$scope.getLastImage2 = function () {
		$scope.lastImage2 = $scope.myUrl + 'lastimage' + '?' + new Date().getTime()
	}
	
	
	//
	//button callbacks
	//
	
	$scope.refresh = function () {
		console.log("refresh");
		$scope.getStatus();
		console.log($scope.status)
	};

	$scope.startstoprecord = function (startstop) {
		console.log("startstoprecord");		
		stopOK = 1;
		if (startstop == 0) {
			stopOK = $window.confirm('Are you sure you want to stop the recording?');
		}
		if (stopOK) {
			$http.get($scope.myUrl + 'record/' + startstop).
        		then(function(response) {
        		    //$scope.status = response.data;
        		});
        }
	};

	$scope.startstopstream = function (startstop) {
		console.log("startstopstream(), startstop:", startstop);
		// if we are stopping, we need to force close the live stream
		if (startstop==1) {
			$scope.hardCloseStream = 0
		} else {
			//startstop == 0
			$scope.hardCloseStream = 1
			callAtTimeout()
		}
		
		$http.get($scope.myUrl + 'stream/' + startstop).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
        //refresh stream
		if (startstop==1) {
			//callAtTimeout()
			$timeout(callAtTimeout, 2000);
		}
	};

	$scope.startstoparm = function (startstop) {
		console.log("startstoparm");		
		$http.get($scope.myUrl + 'arm/' + startstop).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};

	function callAtTimeout() {
		console.log("callAtTimeout()");
		if ($scope.hardCloseStream) {
			console.log('hardCloseStream')
			$scope.myStreamUrl = ''
		} else {
			myStreamUrl = 'http://' + $location.host() + ':8080/stream' + '?' + new Date().getTime()
			$scope.myStreamUrl = $sce.trustAsResourceUrl(myStreamUrl);
		}
	}

	// set the state of an event out (usually led, lick port, motor, etc)
	$scope.eventOutChange = function (name) {
		var isOn = $scope.status.server.eventOut[name] ? 1 : 0
		console.log('eventOutChange:', $scope.status.eventOut)
		url = $scope.myUrl + 'api/eventout/' + name + '/' + isOn
		console.log(url)
		$http.get(url).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	}

	/*
	$scope.iron = function (isOn) {
		console.log("iron");
		$http.get($scope.myUrl + 'irLED/' + isOn).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};
	
	$scope.whiteon = function (isOn) {
		console.log("whiteon");
		$http.get($scope.myUrl + 'whiteLED/' + isOn).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	};
	
	$scope.whiteChange = function () {
		var isOn = $scope.status.lights.whiteLED ? 1 : 0;
		//console.log(isOn);
		$http.get($scope.myUrl + 'whiteLED/' + isOn).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	}
		
	$scope.irChange = function () {
		var isOn = $scope.status.lights.irLED ? 1 : 0;
		//console.log(isOn);
		$http.get($scope.myUrl + 'irLED/' + isOn).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	}
	*/

	/*
	$scope.setConfig = function (param) {
		console.log("setConfig");
		val = $scope.status.fps
		$http.get($scope.myUrl + 'set/' + param + '/' + val).
        	then(function(response) {
        	    $scope.config = response.data;
        	    console.log('$scope.config', $scope.config)
        	});
	}
	*/
	
	$scope.mySubmit = function (param,val) {
		//when checkbox is submitted, val is boolean, convert all value to int
		console.log("mySubmit() " + param + " " + val);
		console.log(typeof val)
		$http.get($scope.myUrl + 'set/' + param + '/' + val).
        	then(function(response) {
        	    $scope.config = response.data;
        	    convertConfig()
        	    console.log('$scope.config', $scope.config)
        	});
	}

	$scope.saveoptions = function () {
		console.log('saveoptions()')
		$http.get($scope.myUrl + 'saveconfig').
        	then(function(response) {
        	    //
        	});
	}
	
	$scope.loaddefaultoptions = function () {
		$http.get($scope.myUrl + 'loadconfigdefaults').
        	then(function(response) {
        	    //reload user configurable config
        	    $scope.getConfig();
        	});
	}
	
	$scope.isState = function(thisState) {
		if ($scope.status) {
			return $scope.status.server.state == thisState
		} else {
			return false
		}
	}
	
	$scope.allowEditeOptions = function() {
		if ($scope.status) {
			return $scope.status.server.state == 'idle'
		} else {
			return false
		}
	}
	
	$scope.simulate = function(cmd) {
		console.log('simulate()', cmd)
		$http.get($scope.myUrl + 'simulate/' + cmd).
        	then(function(response) {
        	    //$scope.config = response.data;
        	    //convertConfig()
        	    //console.log('$scope.config', $scope.config)
        	}, function errorCallback(response) {
        		console.log('simulate() error cmd:', cmd)
        	});
	}
	
	//called once page is loaded
	//angular.element(function () {
	//	console.log('page loading completed');
	//	//$scope.getState();
	//	//$scope.localFPS = $scope.status.fps
	//});

	$scope.getStatus(); //state of homecage server
	$scope.getConfig(); // config user can set
	$interval($scope.getStatus, 400);      	
	
	$interval($scope.getLastImage2, 900);      	

	$scope.hardCloseStream = 0
	
}); //controller
