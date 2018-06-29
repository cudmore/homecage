angular.module('videowall', ['uiSwitch'])
.controller('videowall', function($scope, $window, $http, $location, $interval, $sce, $timeout, $document) {
	
	document.title = 'Video Wall'
	
	console.log('angular.version:', angular.version)
	
	//url of page we loaded
	$scope.myUrl = $location.absUrl(); //with port :5000

	var restPort = 5010;
	
	$scope.numServers = 2;
	$scope.serverList = ['192.168.1.2', '192.168.1.3']
	//$scope.serverList = ['192.168.1.2', '192.168.1.3', '192.168.1.2', '192.168.1.3', '192.168.1.2', '192.168.1.3']

	//
	// manager server list
	//
	$scope.showServerPanel = false
	$scope.showServerConfig = true
	$scope.showServerConfig2 = false
	$scope.showSwarmStatus = false
	$scope.editIPList = false
	$scope.doDebug = false
	
	$scope.toggleVideoPanels = function () {
		$scope.showServerPanel = ! $scope.showServerPanel
	}

	$scope.toggleServerConfig = function () {
		$scope.showServerConfig = ! $scope.showServerConfig
	}
	
	$scope.toggleshowServerConfig2 = function () {
		$scope.showServerConfig2 = ! $scope.showServerConfig2
	}
	
	$scope.toggleEditIPList = function () {
		$scope.editIPList = ! $scope.editIPList
	}
	
	$scope.toggleshowSwarmStatus = function () {
		$scope.showSwarmStatus = ! $scope.showSwarmStatus
	}
	
	$scope.addServer = function() {
		$scope.numServers += 1
		$scope.serverList.push('')
		initVideoWall()
		//$scope.$apply();
	}

	$scope.removeServer = function(idx) {
		removeOK = $window.confirm('Are you sure you want to remove server "' + $scope.serverList[idx] + '"?');
		if (removeOK) {
			$scope.numServers -= 1
			$scope.serverList.splice(idx,1)
			initVideoWall()
			$scope.$apply();
		}
	}

	$scope.setServer = function(idx, str) {
		console.log('$scope.setServer():', idx, str)
		$scope.serverList[idx] = str
		initVideoWall();
	}

	$scope.saveServers = function() {
		console.log('saveServers()')
		//var fs = require('fs');
		var filename = 'output.txt';
		var str = JSON.stringify($scope.serverList, null, 4);
		console.log(str)

		var url = $scope.myUrl + 'saveconfig/' + str
		
		$http.get(url).
        	then(function(response) {
        	    console.log('response.data;', response.data)
        	}, function errorCallback(response) {
        		console.log('saveServers() error')
        	});
	}
	
	$scope.loadServers = function() {
		var url = $scope.myUrl + 'loadconfig'
		$http.get(url).
        	then(function(response) {
        	    console.log('response.data;', response.data)
        	    //var array = JSON.parse(response.data)
        	    var array = response.data
        	    //console.log('array:', array)
        	    $scope.serverList = array
        	    $scope.numServers = array.length
        	    console.log('loadServers()')
        	    console.log('$scope.serverList:', $scope.serverList)
        	    console.log('$scope.numServers:', $scope.numServers)
        	    initVideoWall()
        	}, function errorCallback(response) {
        		console.log('loadServers() error')
        	});
	}
	
	$scope.changeDebug = function(doDebug) {
		console.log('changeDebug()', doDebug)
		//$scope.doDebug = ! $scope.doDebug
		console.log('$scope.doDebug:', $scope.doDebug)
		//initVideoWall()
	}
	//
	// main interface
	//
	function initVideoWall() {
		$scope.videoArray = new Array($scope.numServers)
		for (i=0; i<$scope.numServers; i+=1) {
			id = "v" + i
			$scope.videoArray[i] = {}
			$scope.videoArray[i].myIdx = i
			
			$scope.videoArray[i].restUrl = "http://" + $scope.serverList[i] + ":" + restPort + "/"
			
			getStatus(i) // uses restUrl
						
			//$scope.videoArray[i].animalID = ''
			//$scope.videoArray[i].conditionID = ''

			myStreamUrl = "http://" + $scope.serverList[i] + ":8080/stream"
			$scope.videoArray[i].streamUrl = $sce.trustAsResourceUrl(myStreamUrl)
			$scope.videoArray[i].myStreamUrl = $sce.trustAsResourceUrl(myStreamUrl);
			
			$scope.videoArray[i].image = new Image()
			$scope.videoArray[i].image.src = "" // the image source
			$scope.videoArray[i].image.canvasID = id // the canvas id
			$scope.videoArray[i].image.myIdx = i // the canvas id
			$scope.videoArray[i].image.onload = function(thisEvent) {
				// this is an Image object
				//console.log('this.canvasID:', this.canvasID)
				//console.log('this.src:', this.src)
				var canvas = document.getElementById(this.canvasID);
				if (canvas) {
					var context = canvas.getContext("2d");

					// backgorund color
					context.fillStyle = "blue";
					context.fillRect(0, 0, canvas.width, canvas.height);

					var hRatio = canvas.width / this.width    ;
					var vRatio = canvas.height / this.height  ;
			
					var ratio  = Math.min ( hRatio, vRatio );
			
					context.drawImage(this, 0,0, this.width, this.height, 0,0,this.width*ratio, this.height*ratio);

					//text
					context.font = "18px Arial";
					context.fillStyle = "red";
					var myStr = $scope.videoArray[this.myIdx].status.lastStillTime
					context.fillText(myStr,5,20);
					
					//if ($scope.videoArray[this.myIdx].status.isRecording == false) {
					if (! $scope.isState(this.myIdx, 'recording')) {
						context.font = "56px Arial";
						context.fillStyle = "red";
						var myStr = "Stopped"
					    //context.fillStyle = '#f50';
						//var stoppedWidth = context.measureText(myStr).width;
					    //context.fillRect(180, 200, stoppedWidth, parseInt(56, 10));
						context.fillText(myStr,180,200);
					}
				}			
			};
			//streaming
			$scope.videoArray[i].hardCloseStream = 0
			//$scope.videoArray[i].myStreamUrl = $sce.trustAsResourceUrl(streamList[i]) //'http://' + $location.host() + ':8080/stream';
			$scope.videoArray[i].streamWidth = 640
			$scope.videoArray[i].streamHeight = 480
		
			$scope.videoArray[i].showConfig = false
		}
	}
		
	$scope.isState = function(idx, thisState) {
		//if (idx > 0) {
		//	console.log(idx)
		//}
		//console.log('$scope.videoArray[idx].status:', $scope.videoArray[idx].status)
		if ($scope.videoArray && $scope.videoArray[idx].status) {
			return $scope.videoArray[idx].status.trial.runtime.cameraState == thisState
		} else {
			return false
		}
	}

	$scope.toggleConfig = function(idx) {
		console.log('toggleConfig()', idx)
		$scope.videoArray[idx].showConfig = $scope.videoArray[idx].showConfig === false ? true: false;
	};

    //read the state from homecage backend, do this at an interval
    function getStatus(i) {
		url = $scope.videoArray[i].restUrl
		$http.get(url + 'status').
        	then(function(response) {
        	    $scope.videoArray[i].status = response.data;
        	    $scope.videoArray[i].isAlive = true;

				var tmpWidth = parseInt($scope.videoArray[i].status.trial.config.video.streamResolution.split(',')[0],10)
				var tmpHeight = parseInt($scope.videoArray[i].status.trial.config.video.streamResolution.split(',')[1],10)
				//console.log('tmpWidth:', tmpWidth)
				//console.log('tmpHeight:', tmpHeight)
				$scope.videoArray[i].streamWidth = tmpWidth + (tmpWidth * 0.03)
				$scope.videoArray[i].streamHeight = tmpHeight + (tmpWidth * 0.03)

				//console.log('$scope.videoArray[i].status:', $scope.videoArray[i].status)
				
        	}, function errorCallback(response) {
        		console.log('getStatus() error', url, i)
        	    $scope.videoArray[i].isAlive = false;
        	});
	};

//get rid of .config in general, use .status
/*
    function getConfig(i) {
		url = $scope.videoArray[i].restUrl
		console.log('getConfig() i:', i, 'url:', url)
		$http.get(url + 'status').
        	then(function successCallback(response) {
        	    $scope.videoArray[i].config = response.data;
        	    console.log($scope.videoArray[i])
        	    //$scope.videoArray[i].config.url = url;

				var tmpWidth = parseInt($scope.videoArray[i].config.trial.config.video.streamResolution.split(',')[0],10)
				var tmpHeight = parseInt($scope.videoArray[i].config.trial.config.video.streamResolution.split(',')[1],10)
				//console.log('tmpWidth:', tmpWidth)
				//console.log('tmpHeight:', tmpHeight)
				$scope.videoArray[i].streamWidth = tmpWidth + (tmpWidth * 0.03)
				$scope.videoArray[i].streamHeight = tmpHeight + (tmpWidth * 0.03)
        	}, function errorCallback(response) {
        		console.log('getConfig() error', url, i)
        	});
	};
*/

	$scope.refreshStatusButton = function() {
		console.log('refreshStatusButton()')
		for (i=0; i<$scope.numServers; i+=1) {
			getStatus(i)
		}
		console.log($scope.videoArray)
	}
	
	//
	// RECORDING
	$scope.startstoprecord = function (idx, startstop) {
		console.log("startstoprecord()", idx, startstop);		
		stopOK = 1;
		if (startstop == 0) {
			stopOK = $window.confirm('Are you sure you want to stop the recording?');
		}
		if (stopOK) {
			if (startstop) {
				url = $scope.videoArray[idx].restUrl + 'api/action/startRecord'
			} else {
				url = $scope.videoArray[idx].restUrl + 'api/action/stopRecord'
			}
			console.log(url)
			$http.get(url).
        		then(function(response) {
        	    	$scope.videoArray[idx].status = response.data;
        		}, function errorCallback(response) {
        			console.log('startstoprecord() error url:', url)
        		});
        }
	};

	//
	//STREAMING
	$scope.startstopstream = function (idx, startstop) {
		console.log("startstopstream()", idx, startstop);		
		// if we are stopping, we need to force close the live stream
		if (startstop==1) {
			$scope.videoArray[idx].hardCloseStream = 0
			url = $scope.videoArray[idx].restUrl + 'api/action/startStream'
		} else {
			//startstop == 0
			$scope.videoArray[idx].hardCloseStream = 1
			callAtTimeout(idx)
			url = $scope.videoArray[idx].restUrl + 'api/action/stopStream'
		}
		
		$http.get(url).
        	then(function(response) {
        	    $scope.videoArray[idx].status = response.data;
        	}, function errorCallback(response) {
        		console.log('startstopstream() error url:', url)
        	});
        //refresh stream
		if (startstop==1) {
			//callAtTimeout()
			$timeout(callAtTimeout(idx), 2000);
		}
	};

	//
	//change led status
//final
    $scope.submitConfigForm = function(idx) {
        url = $scope.videoArray[idx].restUrl + 'api/submit/configparams'
        console.log('submitConfigForm(), url:', url)
        $http.post(url, JSON.stringify($scope.videoArray[idx].status.trial.config)).
        	then(function(response) {
        		$scope.videoArray[idx].status = response.data
        	});
    };

    $scope.submitLEDForm = function(idx) {
        url = $scope.videoArray[idx].restUrl + 'api/submit/ledparams'
        console.log('submitLEDForm(), url:', url)
        $http.post(url, JSON.stringify($scope.videoArray[idx].status.trial.config)).
        	then(function(response) {
        		$scope.videoArray[idx].status = response.data
        	});
    };

    $scope.submitAnimalForm = function(idx) {
        //console.log('submitConfigForm()', $scope.configData, $scope.configData.$valid);
        url = $scope.videoArray[idx].restUrl + 'api/submit/animalparams'
        console.log('submitAnimalForm(), url:', url)
        console.log($scope.videoArray[idx].status.trial.config)
        $http.post(url, JSON.stringify($scope.videoArray[idx].status.trial.config)).
        	then(function(response) {
        		$scope.videoArray[idx].status = response.data
        	});
    };


	function callAtTimeout(idx) {
		console.log("callAtTimeout()", idx);
		if ($scope.videoArray[idx].hardCloseStream) {
			console.log('hardCloseStream', idx)
			$scope.videoArray[idx].myStreamUrl = ''
		} else {
			//myStreamUrl = streamList[idx] + '?' + new Date().getTime() //'http://' + $location.host() + ':8080/stream' + '?' + new Date().getTime()
			myStreamUrl = $scope.videoArray[idx].streamUrl + '?' + new Date().getTime()
			$scope.videoArray[idx].myStreamUrl = $sce.trustAsResourceUrl(myStreamUrl);
		}
	}

	//
	// call this at an interval
	$scope.getLastImage = function () {
		for (i=0; i<$scope.numServers; i+=1) {
			//getStatus($scope.videoArray[i].restUrl, i)
			
			//getConfig($scope.videoArray[i].restUrl, i)
			
			$scope.videoArray[i].image.src = $scope.videoArray[i].restUrl + 'lastimage' + '?' + new Date().getTime()
		}
	}

	$scope.loadServers()
	//initVideoWall()
	
	//treadmill put this back in
	//$interval($scope.getLastImage, 900);      	
	
	//$scope.hardCloseStream = 0

	myUpdate = function() {
		for (i=0; i<$scope.numServers; i+=1) {
			getStatus(i)
		}
	}	
	$interval(myUpdate, 400); 
}); //controller
