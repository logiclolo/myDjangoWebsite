var prev_selected_link = null;

function set_iframe(link)
{
	document.getElementById('content_frame').src = link;
}

function on_load()
{
	cookies_init();

	var prev_link = get_cookie('prevlink');
	if (!prev_link)
	{
		var employee_page_link = document.getElementById('employee');
		set_iframe(employee_page_link.href);
		set_cookie('prevlink', employee_page_link.id);
		select(employee_page_link);

		return;
	}

	var link = document.getElementById(prev_link);
	set_iframe(link.href);
	select(link);
}

function select(link)
{
	link.setAttribute('class', 'selected');

	if (prev_selected_link)
		prev_selected_link.setAttribute('class', '');
	prev_selected_link = link;
}

function on_click(link)
{
	if (prev_selected_link === link)
		return false;

	set_iframe(link.href);
	set_cookie('prevlink', link.id);
	select(link);

	return false;
}
