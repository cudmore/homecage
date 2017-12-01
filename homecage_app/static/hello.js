
angular.module('demo', ['uiSwitch'])
.controller('Hello', function($scope, $window, $http, $location, $interval, $sce, $timeout) {
	
	console.log('angular.version:', angular.version)
	
	//url of page we loaded
	$scope.myUrl = $location.absUrl(); //with port :5000
	
    myStreamUrl = 'http://' + $location.host() + ':8080/stream';
    $scope.myStreamUrl0 = myStreamUrl
    $scope.myStreamUrl = $sce.trustAsResourceUrl(myStreamUrl);
	
	//todo: rewrite these to just be inline with logic in button html
	$scope.showOptions = false;
	$scope.toggleOptions = function() {
		console.log('toggleOptions()')
		$scope.showOptions = $scope.showOptions === false ? true: false;
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
        	    $scope.videofilelist = $scope.status.videofilelist
        	    $scope.status.videofilelist = ''
        	    
        	    //calculate web page iframe for stream
        	    var tmpWidth = $scope.status.config.stream.streamResolution[0]
        	    var tmpHeight = $scope.status.config.stream.streamResolution[1]
        	    $scope.streamWidth = tmpWidth + (tmpWidth * 0.03)
        	    $scope.streamHeight = tmpHeight + (tmpWidth * 0.03) 
        	});
	};

    //read user editable options
    $scope.getParams = function () {
		$http.get($scope.myUrl + 'params').
        	then(function(response) {
        	    $scope.params = response.data;
        	});
	};

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
		var isOn = $scope.status.whiteLED ? 1 : 0;
		//console.log(isOn);
		$http.get($scope.myUrl + 'whiteLED/' + isOn).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	}
	
	$scope.irChange = function () {
		var isOn = $scope.status.irLED ? 1 : 0;
		//console.log(isOn);
		$http.get($scope.myUrl + 'irLED/' + isOn).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	}

	$scope.setParam = function (param) {
		console.log("setParam");
		val = $scope.status.fps
		$http.get($scope.myUrl + 'set/' + param + '/' + val).
        	then(function(response) {
        	    //$scope.status = response.data;
        	});
	}

	$scope.mySubmit = function (param,val) {
		console.log("mySubmit() " + param + " " + val);
		$http.get($scope.myUrl + 'set/' + param + '/' + val).
        	then(function(response) {
        	    //$scope.status = response.data;
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
        	    //
        	});
	}
	
	//called once page is loaded
	//angular.element(function () {
	//	console.log('page loading completed');
	//	//$scope.getState();
	//	//$scope.localFPS = $scope.status.fps
	//});

	$scope.getStatus(); //state of homecage server
	$scope.getParams(); // params user can set
	$interval($scope.getStatus, 900);      	
	
	$interval($scope.getLastImage2, 900);      	

	$scope.hardCloseStream = 0
	
}); //controller
