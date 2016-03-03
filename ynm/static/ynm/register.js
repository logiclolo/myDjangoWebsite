angular.module('register', ['ngCookies']);

function on_load()
{
	document.getElementById('id_camera_maintainer').focus();
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

function query_prizes(scope, http, winners)
{
	angular.forEach(winners, function(element, idx) {
		http.get('/lottery/prize/?winner_jobid=' + element.jobid).
		success(function(data) {
			if (data.status == 'ok')
			{
				translate(data.data);
				element.prizes = data.data;
			}
			else
			{
				element.prizes = null;
			}
		}).
		error(function (data, status, headers, config) {
			var msg = data || errmsg("Connection failure");
			alert(msg + "\n" + config.url);
		});
	});
}

function query_name(scope, http, name)
{
	http.get('/lottery/employee/?name=' + encodeURIComponent(name)).
	success(function(data) {
		if (data.status == 'ok')
		{
			scope.employees = data.data;
			scope.hasdata = true;

			query_prizes(scope, http, data.data);
		}
		else if (data.status == 'error')
		{
			scope.employees = null;
			scope.hasdata = false;
		}
	}).
	error(function (data, status, headers, config) {
		var msg = data || errmsg("Connection failure");
		alert(msg + "\n" + config.url);
	});
}

function query_id(scope, http, id)
{
	http.get('/lottery/employee/?id=' + id).
	success(function(data) {
		if (data.status == 'ok')
		{
			scope.employees = data.data;
			scope.hasdata = true;

			query_prizes(scope, http, data.data);
		}
		else if (data.status == 'error')
		{
			scope.employees = null;
			scope.hasdata = false;
		}
	}).
	error(function (data, status, headers, config) {
		var msg = data || errmsg("Connection failure");
		alert(msg + "\n" + config.url);
	});
}

function query_id_fuzzy(scope, http, text)
{
	if (text != scope.input)
		return;

	http.get('/lottery/employee/?fuzzy_id=' + text).
	success(function(data) {
		if (data.status == 'ok')
		{
			scope.employees = data.data;
			scope.hasdata = true;

			query_prizes(scope, http, data.data);
		}
		else if (data.status == 'error')
		{
			scope.employees = null;
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

function register_ctrl($scope, $http, $cookies, $timeout)
{
	$scope.hasdata = false;
	$scope.query_employee = function() {
		var text = $scope.input

		if (text.toLowerCase().indexOf('vv') < 0 && text.toLowerCase().indexOf('va') < 0)
		{
			// We expect the name has at least 2 characters.
			if (text.length < 2)
				return;

			if (text.search(/\D/) < 0)
			{
				$timeout(function () {
					query_id_fuzzy($scope, $http, text);
				}, 400);
			}
			else
				query_name($scope, $http, text);
		}

		var num = text.slice(2);
		if (num.length < 4)
			return;

		if (num.search(/\D/) >= 0)
			return;

		query_id($scope, $http, text.toLowerCase());
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
