var msgs = {
	'Not found': '找不到',
	'Invalid method': '不正確的方法',
	'Invalid data format': '非法的資料格式',
	'Duplicated winner': '重覆的中獎人',
	'Prize not found': '找不到獎項',
	'Employee not found': '找不到員工資料',
	'Donator should not be empty': '捐贈主管姓名不能為空',
	'Custom donator should not be empty': '自訂輸入不能為空',
	'Prize name should not be empty': '獎項名稱不能為空',
	'Connection failure': '連線失敗',
};

function errmsg(msg)
{
	if (msgs[msg] == undefined)
		return msg;

	return msgs[msg];
}
