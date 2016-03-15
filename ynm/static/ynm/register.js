angular.module('register', ['ngCookies']);

function on_load()
{
	document.getElementById('maintainer').focus();
}

function on_change(input)
{
	input.select();
}

function register_ctrl($scope, $http, $cookies, $timeout)
{
	$scope.register_hasdata = true;
	$scope.register_done_hasdata = false;

	$scope.submit_form = function() {
		$http.post('/ynm/register/', $scope.camera).
		success(function(data){
			if (data.status == 'ok')
			{
				if (data.data.length == 0)
				{
					scope.cameras = null;
				}
				else
				{
					$scope.register_hasdata = false;
					$scope.register_done_hasdata = true;
					$scope.cameras = data.data
				}
			}
			else if (data.status == 'error')
			{
				scope.cameras = null;
			}
		}).
		error(function (data, status, headers, config) {
			var msg = data || errmsg("Connection failure");
			alert(msg + "\n" + config.url);
		});
	};
}
