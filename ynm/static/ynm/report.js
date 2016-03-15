angular.module('report', ['ngCookies']);

function on_load()
{
	document.getElementById('input').focus();
}

function on_change(input)
{
	input.select();
}

function query_maintainer(scope, http, name)
{
	http.get('/ynm/report/?maintainer=' + encodeURIComponent(name)).
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

	http.get('/ynm/report/?modelname=' + text).
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

function report_ctrl($scope, $http, $cookies, $timeout)
{
	$scope.hasdata = false;

	$scope.query_report = function() {
		var text = $scope.input

		// we expact the name has at least 2 characters
		if (text.length < 2)
			return;

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
