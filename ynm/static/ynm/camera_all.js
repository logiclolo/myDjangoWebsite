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
	$scope.update_hasdata = false;
	$scope.update_done_hasdata = false;
	query_camera_all($scope, $http);

	$scope.on_click = function() {
		$scope.hasdata = false;
		$scope.search = false;
		$scope.update_hasdata= true;

		$scope.camera = this.camera
	};

	$scope.submit_form = function() {
		$http.post('/ynm/update/', $scope.camera).
		success(function(data){
			if (data.status == 'ok')
			{
				if (data.data.length == 0)
				{
					scope.cameras = null;
				}
				else
				{
					$scope.update_hasdata = false;
					$scope.update_done_hasdata = true;
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
