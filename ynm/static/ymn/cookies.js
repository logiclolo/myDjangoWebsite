var cookie_arr = [];

function cookie_join(array)
{
	var tmp = '';

	for (var i = 0; i < array.length; i++)
	{
		tmp += array[i];
		tmp += ';';
	}

	return tmp;
}

function set_cookie(name, value)
{
	var found = false;

	for (var i = 0; i < cookie_arr.length; i++)
	{
		if (cookie_arr[i].indexOf(name) >= 0)
		{
			cookie_arr[i] = name + '=' + value;
			found = true;
			break;
		}
	}

	if (!found)
	{
		cookie_arr.push(name + '=' + value);
	}

	document.cookie = cookie_join(cookie_arr);
}

function get_cookie(name)
{
	for (var i = 0; i < cookie_arr.length; i++)
	{
		if (cookie_arr[i].indexOf(name) >= 0)
		{
			var idx = cookie_arr[i].indexOf('=');
			if (idx > 0)
			{
				return cookie_arr[i].slice(idx + 1);
			}

			return null;
		}
	}

	return null;
}

function cookies_init()
{
	var str = document.cookie;
	if (str.length != 0)
		cookie_arr = str.split(';');

	for (var i = 0; i < cookie_arr.length; i++)
		cookie_arr[i] = cookie_arr[i].trim();
}
