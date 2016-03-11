angular.module('camera', ['ngCookies']);

function on_load($scope, $http)
{
	//document.getElementById('input').focus();
	query_all($scope, $http)
}

function on_change(input)
{
	input.select();
}

function translate(data)
{
	for (var i = 0; i < data.length; i++)
	{
		var d = data[i];

		if (d['receiving_status'] == 'inqueue')
			d['receiving_status'] = '待領中 (序號 ' + d['queue_id'] + ')';
		else if (d['receiving_status'] == 'received')
			d['receiving_status'] = '已領取';
	}
}

function query_all(scope, http)
{
	http.get('/ynm/camera/')
	success(function(data) {
		if (data.status == 'ok')
		{
			scope.cameras = data.data;
			scope.hasdata = true;
		}
		else if (data.status == 'error')
		{
			scope.cameras = null;
			scope.hasdata = false;
		}
	}).
	error(function (data, status, headers, config) {
		var msg = data || errmsg("Connection failure");
		alert(msg + "\n" + config.url);
	});
}

function query_maintainer(scope, http, name)
{
	http.get('/ynm/camera/?maintainer=' + encodeURIComponent(name)).
	success(function(data) {
		if (data.status == 'ok')
		{
			scope.reports = data.data;
			scope.hasdata = true;
		}
		else if (data.status == 'error')
		{
			scope.reports = null;
			scope.hasdata = false;
		}
	}).
	error(function (data, status, headers, config) {
		var msg = data || errmsg("Connection failure");
		alert(msg + "\n" + config.url);
	});
}

function query_modelname(scope, http, text)
{
	if (text != scope.input)
		return;

	http.get('/ynm/camera/?modelname=' + text).
	success(function(data) {
		if (data.status == 'ok')
		{
			scope.reports = data.data;
			scope.hasdata = true;
		}
		else if (data.status == 'error')
		{
			scope.reports = null;
			scope.hasdata = false;
		}
	}).
	error(function (data, status, headers, config) {
		var msg = data || errmsg("Connection failure");
		alert(msg + "\n" + config.url);
	});
}

function submit_queue(scope, http, prize)
{
	var obj = new Object();
	obj.serial = prize.serial;
	obj.phase_alias = prize.phase_alias;

	var json = angular.toJson(obj);

	http.post('/lottery/add_queue/', json).
	success(function (data) {
		if (data.status == 'ok')
		{
			prize.errmsg = null;
			prize.is_sync = true;
			prize.queue_id = ' (序號 ' + data.data.queue_id + ')';
		}
		else
		{
			prize.errmsg = errmsg(data.reason);
			prize.is_sync = false;
		}
	}).
	error(function (data, status, headers, config) {
		var msg = errmsg("Connection failure") + ': ' + status;
		alert(msg);
	});
}

function camera_ctrl($scope, $http, $cookies, $timeout)
{
	$scope.hasdata = false;

	$scope.query_report = function() {
		var text = $scope.input

		if (text.search(/\d/) < 0) // model name
		{
			$timeout(function () {
				query_maintainer($scope, $http, text);
			}, 400);
		}
		else 
		{
			query_modelname($scope, $http, text);
		}
	};

	$scope.submit_queue = function (prize) {
		submit_queue($scope, $http, prize);
	};

	$scope.receivable = function (prize) {
		if (!prize.onsite)
			return false;

		if (prize.receiving_status == '')
			return true;
		else
			return false;
	};
}
