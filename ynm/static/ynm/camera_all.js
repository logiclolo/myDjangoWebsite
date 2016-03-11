function query_camera_all(scope, http)
{
	http.get('/ynm/camera/').
	success(function(data) {
		scope.loaddata = false;
		if (data.status == 'ok')
		{
			if (data.data.length == 0)
			{
				scope.cameras = null;
				scope.hasdata = false;
				scope.nodata = true;
			}
			else
			{
				scope.cameras = data.data;
				scope.hasdata = true;
				scope.nodata = false;
			}
		}
		else if (data.status == 'error')
		{
			scope.cameras = null;
			scope.hasdata = false;
			scope.nodata = true;
		}
	}).
	error(function (data, status, headers, config) {
		var msg = data || errmsg("Connection failure");
		alert(msg + "\n" + config.url);
	});
}

function camera_all_ctrl($scope, $http)
{
	$scope.hasdata = false;
	$scope.nodata = false;
	$scope.loaddata = true;
	$scope.search = true;
	$scope.updatedata = false;
	query_camera_all($scope, $http);

	$scope.on_click = function() {
		$scope.hasdata = false;
		$scope.search = false;
		$scope.updatedata = true;

		$scope.camera = this.camera
	};
}
